from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.frontend import (
    SPAStaticFiles,
    development_cors_origins,
    is_public_unauthenticated_browser_path,
)
from app.main import app as planner_app


def test_public_entry_points_are_exact_and_production_has_no_cors_origins():
    assert is_public_unauthenticated_browser_path("/lecturer-review/")
    assert is_public_unauthenticated_browser_path("/login/")
    assert is_public_unauthenticated_browser_path("/assets/app.js")
    assert not is_public_unauthenticated_browser_path("/lecturer-review/admin")
    assert not is_public_unauthenticated_browser_path("/login/unexpected")
    assert development_cors_origins(production=True) == []
    assert development_cors_origins(production=False) == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_development_cors_preflight_reaches_cors_before_planner_authentication():
    response = TestClient(planner_app).options(
        "/api/auth/login",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-protection",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


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
