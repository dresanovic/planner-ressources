from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.frontend import SPAStaticFiles


def _frontend_client(tmp_path):
    (tmp_path / "index.html").write_text(
        "<!doctype html><title>Planner frontend</title>",
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('planner')", encoding="utf-8")

    app = FastAPI()

    @app.get("/api/example")
    def api_example():
        return {"source": "api"}

    app.mount("/", SPAStaticFiles(directory=tmp_path, html=True), name="frontend")
    return TestClient(app)


def test_serves_frontend_root_and_assets(tmp_path):
    client = _frontend_client(tmp_path)

    root = client.get("/", headers={"Accept": "text/html"})
    asset = client.get("/assets/app.js")

    assert root.status_code == 200
    assert "Planner frontend" in root.text
    assert asset.status_code == 200
    assert "console.log" in asset.text


def test_serves_index_for_browser_route_without_shadowing_api(tmp_path):
    client = _frontend_client(tmp_path)

    frontend_route = client.get(
        "/lecturer-review/",
        headers={"Accept": "text/html"},
    )
    api_route = client.get("/api/example")
    missing_api_route = client.get(
        "/api/missing",
        headers={"Accept": "text/html"},
    )

    assert frontend_route.status_code == 200
    assert "Planner frontend" in frontend_route.text
    assert api_route.json() == {"source": "api"}
    assert missing_api_route.status_code == 404


def test_missing_non_html_resource_remains_not_found(tmp_path):
    client = _frontend_client(tmp_path)

    response = client.get(
        "/missing.json",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 404
