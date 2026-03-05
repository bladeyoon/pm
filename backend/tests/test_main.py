from pathlib import Path

from fastapi.testclient import TestClient

from app.main import HELLO_PAGE, create_app, resolve_frontend_asset


def test_root_serves_hello_html_without_static_build() -> None:
    client = TestClient(create_app(frontend_dir=None))
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Hello from FastAPI" in response.text
    assert response.text == HELLO_PAGE


def test_health_endpoint_returns_ok_payload() -> None:
    client = TestClient(create_app(frontend_dir=None))
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "pm-mvp-backend"}


def test_resolve_frontend_asset_handles_existing_and_traversal(tmp_path: Path) -> None:
    frontend_dir = tmp_path / "out"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    nested = frontend_dir / "_next" / "static"
    nested.mkdir(parents=True, exist_ok=True)
    index = frontend_dir / "index.html"
    asset = nested / "chunk.js"
    index.write_text("<h1>Kanban Studio</h1>", encoding="utf-8")
    asset.write_text("console.log('chunk')", encoding="utf-8")

    assert resolve_frontend_asset(frontend_dir, "") == index
    assert resolve_frontend_asset(frontend_dir, "_next/static/chunk.js") == asset
    assert resolve_frontend_asset(frontend_dir, "../secrets.txt") is None


def test_root_serves_static_frontend_when_available(tmp_path: Path) -> None:
    frontend_dir = tmp_path / "out"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    (frontend_dir / "index.html").write_text(
        "<!doctype html><html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    (frontend_dir / "file.svg").write_text("<svg></svg>", encoding="utf-8")
    client = TestClient(create_app(frontend_dir=frontend_dir))

    root_response = client.get("/")
    asset_response = client.get("/file.svg")
    spa_fallback_response = client.get("/some/client/route")

    assert root_response.status_code == 200
    assert "Kanban Studio" in root_response.text
    assert asset_response.status_code == 200
    assert "<svg" in asset_response.text
    assert spa_fallback_response.status_code == 200
    assert "Kanban Studio" in spa_fallback_response.text
