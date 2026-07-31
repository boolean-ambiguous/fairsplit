from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db

BASE_DIR = Path(__file__).parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    from app.routes.dashboard import router as dashboard_router
    from app.routes.groups import router as groups_router

    app = FastAPI(title="FairSplit", lifespan=lifespan)
    app.include_router(groups_router)
    app.include_router(dashboard_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    if FRONTEND_DIST.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=FRONTEND_DIST / "assets"),
            name="assets",
        )

        @app.get("/{full_path:path}")
        def spa(full_path: str) -> FileResponse:
            return FileResponse(FRONTEND_DIST / "index.html")

    return app


app = create_app()
