import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    """Sliding-window request limiter, keyed by an arbitrary string (e.g. an
    IP address). In-memory and per-process — fine for this app's
    single-instance deployment (SQLite on one disk already rules out running
    more than one instance), and resets on deploy, which is an acceptable
    tradeoff for abuse mitigation rather than a security boundary."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True


signup_ip_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=900)
