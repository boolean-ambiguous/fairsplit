import os

# The origin the frontend SPA is served from. Magic-link emails point here.
# In dev the frontend runs on Vite's own port; in prod FastAPI serves the
# built SPA itself, so the API's own origin is correct.
FRONTEND_BASE_URL = os.environ.get("FAIRSPLIT_FRONTEND_URL", "http://localhost:5173")
