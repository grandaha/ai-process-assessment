from fastapi.testclient import TestClient

from cockpit.server import create_app


def _client(engagement_root):
    return TestClient(create_app(engagement_root))


def test_state_endpoint_returns_snapshot(engagement):
    root = engagement("scope.md")
    r = _client(root).get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert body["engagement"] == "acme-engagement"
    assert body["progress"]["done"] == 1


def test_index_html_served_at_root(engagement):
    r = _client(engagement()).get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_file_endpoint_returns_contents(engagement):
    root = engagement(**{"scope.md": "# Scope\nHello"})
    r = _client(root).get("/api/file", params={"path": "scope.md"})
    assert r.status_code == 200
    assert r.json() == {"path": "scope.md", "content": "# Scope\nHello"}


def test_file_endpoint_404_for_missing(engagement):
    r = _client(engagement()).get("/api/file", params={"path": "nope.md"})
    assert r.status_code == 404


def test_file_endpoint_rejects_traversal(engagement):
    r = _client(engagement()).get("/api/file", params={"path": "../secret.md"})
    assert r.status_code == 400


import json as _json

import anyio

from cockpit.watch import snapshot_events


def test_events_route_is_registered_as_event_stream(engagement):
    app = create_app(engagement("scope.md"))
    routes = {r.path: r for r in app.routes}
    assert "/api/events" in routes


def test_file_raw_serves_html(engagement):
    root = engagement(**{"deliverable.html": "<h1>Deck</h1>"})
    r = _client(root).get("/api/file-raw", params={"path": "deliverable.html"})
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Deck" in r.text


def test_file_raw_rejects_traversal(engagement):
    r = _client(engagement()).get("/api/file-raw", params={"path": "../secret.md"})
    assert r.status_code == 400


def test_snapshot_events_emits_initial_snapshot(engagement):
    """The SSE generator yields the current snapshot as its first frame.

    Driven directly rather than through TestClient: snapshot_events is an
    infinite stream (it never returns until the folder watch is cancelled),
    and Starlette's TestClient deadlocks on such streams at context exit. We
    pull only the first frame — emitted before awatch is ever entered — then
    close the generator, which verifies the real behaviour the route relies on.
    """
    root = engagement("scope.md")

    async def first_frame():
        gen = snapshot_events(root)
        try:
            return await gen.__anext__()
        finally:
            await gen.aclose()

    frame = anyio.run(first_frame)
    assert frame.startswith("data:")
    assert frame.endswith("\n\n")
    payload = _json.loads(frame[len("data:"):].strip())
    assert payload["progress"]["done"] == 1
