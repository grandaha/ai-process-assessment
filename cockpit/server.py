"""FastAPI app for the cockpit. One app instance is bound to one engagement folder."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cockpit.state import read_state

WEB_DIR = Path(__file__).parent / "web"


def create_app(engagement_dir) -> FastAPI:
    root = Path(engagement_dir).resolve()
    app = FastAPI(title="Engagement Cockpit")

    @app.get("/api/state")
    def state() -> dict:
        return read_state(root)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
    return app
