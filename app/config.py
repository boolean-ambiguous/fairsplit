import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

_FRONTEND_URL_OVERRIDE = os.environ.get("FAIRSPLIT_FRONTEND_URL")
_DEV_FRONTEND_URL = "http://localhost:5173"


def resolve_frontend_base_url(request_base_url: str) -> str:
    """Where magic-link emails should point.

    Priority: an explicit FAIRSPLIT_FRONTEND_URL env var always wins (real
    deployments — reverse proxies, custom domains, split origins). Otherwise,
    if the built frontend exists, FastAPI is serving the SPA itself from its
    own origin (see app/main.py) — use the incoming request's own origin, so
    it's correct whatever host/port it's actually reachable at with zero
    configuration. Otherwise (frontend/dist missing — dev split mode, `npm
    run dev` running on its own port) fall back to Vite's default dev port.
    """
    if _FRONTEND_URL_OVERRIDE:
        return _FRONTEND_URL_OVERRIDE.rstrip("/")
    if FRONTEND_DIST.exists():
        return request_base_url.rstrip("/")
    return _DEV_FRONTEND_URL
