"""FastAPI app for the cockpit. One app instance is bound to one engagement folder."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from cockpit.state import read_state
from cockpit.watch import snapshot_events

WEB_DIR = Path(__file__).parent / "web"


def _resolve_in_root(root: Path, path: str) -> Path:
    """Resolve a request path against the engagement root, refusing escapes.

    Single source of truth for the file-serving guard so the two file routes
    cannot drift apart on this security-critical check. Raises 400 if the path
    escapes the engagement folder, 404 if it is not an existing file.
    """
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise HTTPException(status_code=400, detail="path escapes engagement folder")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return target


def create_app(engagement_dir) -> FastAPI:
    root = Path(engagement_dir).resolve()
    app = FastAPI(title="Engagement Cockpit")

    @app.get("/api/state")
    def state() -> dict:
        return read_state(root)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    @app.get("/favicon.ico")
    def favicon() -> Response:
        # The SPA ships no icon; answer the browser's automatic request with
        # 204 No Content so it doesn't log a 404 on every page load.
        return Response(status_code=204)

    @app.get("/api/events")
    async def events() -> StreamingResponse:
        return StreamingResponse(
            snapshot_events(root), media_type="text/event-stream"
        )

    @app.get("/api/file")
    def file(path: str = Query(...)) -> dict:
        target = _resolve_in_root(root, path)
        return {"path": path, "content": target.read_text()}

    @app.get("/api/file-raw")
    def file_raw(path: str = Query(...)) -> FileResponse:
        return FileResponse(_resolve_in_root(root, path))

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
    return app
