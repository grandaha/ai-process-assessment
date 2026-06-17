"""FastAPI app for the cockpit. One app instance is bound to one engagement folder."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
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

    @app.get("/api/file")
    def file(path: str = Query(...)) -> dict:
        target = (root / path).resolve()
        if root not in target.parents and target != root:
            raise HTTPException(status_code=400, detail="path escapes engagement folder")
        if not target.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        return {"path": path, "content": target.read_text()}

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
    return app
