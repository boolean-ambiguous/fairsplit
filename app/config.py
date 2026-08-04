import ipaddress
import os
from pathlib import Path
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

_FRONTEND_URL_OVERRIDE = os.environ.get("FAIRSPLIT_FRONTEND_URL")
_DEV_FRONTEND_URL = "http://localhost:5173"


class UntrustedRequestOriginError(Exception):
    """Raised when auto-detecting the frontend origin from a request would
    mean trusting an unverifiable, attacker-controlled Host header.

    Only raised in "local production-style" mode (frontend/dist present, no
    FAIRSPLIT_FRONTEND_URL override) when the request's Host doesn't parse
    as a loopback/private-network IP and isn't literally "localhost". The
    operator should set FAIRSPLIT_FRONTEND_URL explicitly in that case.
    """


def _is_trusted_local_host(hostname: str | None) -> bool:
    """True if hostname is loopback/private-network or literally
    "localhost" — i.e. plausibly "this machine" or "my LAN", the only
    origins we can auto-detect without a reverse proxy in front of us."""
    if hostname is None:
        return False
    if hostname == "localhost":
        return True
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return addr.is_private


def resolve_frontend_base_url(request_base_url: str, request_origin: str | None = None) -> str:
    """Where magic-link emails should point.

    Priority: an explicit FAIRSPLIT_FRONTEND_URL env var always wins (real
    deployments — reverse proxies, custom domains, split origins). Otherwise,
    if the built frontend exists, FastAPI is serving the SPA itself from its
    own origin (see app/main.py) — use the incoming request's own origin, so
    it's correct whatever host/port it's actually reachable at with zero
    configuration, PROVIDED that origin is loopback or private-network (i.e.
    plausibly "this machine" / "my LAN"). The Host header is otherwise fully
    attacker-controlled and unverifiable (no reverse proxy/TrustedHostMiddleware
    sits in front of this app), and embedding it unchecked in a mailed
    magic-link URL would let an attacker redirect a victim's login token to a
    domain of the attacker's choosing — see UntrustedRequestOriginError.
    Otherwise (frontend/dist missing — dev split mode, `npm run dev` running
    on its own port, e.g. 5173/5174/... depending on what's free) the backend
    and frontend are on different origins, so request_base_url is useless
    here — it's the *backend's* own address. Instead use the browser-supplied
    Origin header, which names the actual frontend dev-server port, subject
    to the same loopback/private/localhost trust check. Fall back to Vite's
    default dev port only if that header is missing or untrusted.
    """
    if _FRONTEND_URL_OVERRIDE:
        return _FRONTEND_URL_OVERRIDE.rstrip("/")
    if FRONTEND_DIST.exists():
        hostname = urlsplit(request_base_url).hostname
        if not _is_trusted_local_host(hostname):
            raise UntrustedRequestOriginError(
                f"Refusing to build a magic-link URL from untrusted request "
                f"host {hostname!r}. Set FAIRSPLIT_FRONTEND_URL to the app's "
                f"real public URL."
            )
        return request_base_url.rstrip("/")
    if request_origin:
        hostname = urlsplit(request_origin).hostname
        if _is_trusted_local_host(hostname):
            return request_origin.rstrip("/")
    return _DEV_FRONTEND_URL
