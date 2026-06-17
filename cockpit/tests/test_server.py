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
