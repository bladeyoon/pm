from pathlib import Path

from fastapi.testclient import TestClient

from app.board_store import DEFAULT_BOARD
from app.main import HELLO_PAGE, create_app, resolve_frontend_asset


def test_root_serves_hello_html_without_static_build(tmp_path: Path) -> None:
    client = TestClient(create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3"))
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Hello from FastAPI" in response.text
    assert response.text == HELLO_PAGE


def test_health_endpoint_returns_ok_payload(tmp_path: Path) -> None:
    client = TestClient(create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3"))
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "pm-mvp-backend"}


def test_database_bootstrap_creates_file_and_seed_board(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "pm.sqlite3"
    client = TestClient(create_app(frontend_dir=None, db_path=db_path))

    response = client.get("/api/board/user")

    assert db_path.exists()
    assert response.status_code == 200
    assert response.json()["board"] == DEFAULT_BOARD


def test_get_board_for_unknown_user_creates_default_board(tmp_path: Path) -> None:
    client = TestClient(create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3"))

    response = client.get("/api/board/new-user")

    assert response.status_code == 200
    assert response.json()["username"] == "new-user"
    assert response.json()["board"] == DEFAULT_BOARD


def test_update_board_round_trip(tmp_path: Path) -> None:
    client = TestClient(create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3"))
    updated_board = {
        "columns": [{"id": "col-1", "title": "Todo", "cardIds": ["card-1"]}],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Write API tests",
                "details": "Ensure put/get round-trip works.",
            }
        },
    }

    put_response = client.put("/api/board/user", json={"board": updated_board})
    get_response = client.get("/api/board/user")

    assert put_response.status_code == 200
    assert put_response.json()["board"] == updated_board
    assert get_response.status_code == 200
    assert get_response.json()["board"] == updated_board


def test_update_board_rejects_invalid_payload(tmp_path: Path) -> None:
    client = TestClient(create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3"))
    invalid_board = {
        "columns": [{"id": "col-1", "title": "Todo", "cardIds": ["card-missing"]}],
        "cards": {},
    }

    response = client.put("/api/board/user", json={"board": invalid_board})

    assert response.status_code == 422
    assert "missing from cards" in response.json()["detail"]


def test_board_route_rejects_blank_username(tmp_path: Path) -> None:
    client = TestClient(create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3"))

    response = client.get("/api/board/%20%20")

    assert response.status_code == 422
    assert "username must be non-empty" in response.json()["detail"]


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
    client = TestClient(create_app(frontend_dir=frontend_dir, db_path=tmp_path / "pm.sqlite3"))

    root_response = client.get("/")
    asset_response = client.get("/file.svg")
    spa_fallback_response = client.get("/some/client/route")

    assert root_response.status_code == 200
    assert "Kanban Studio" in root_response.text
    assert asset_response.status_code == 200
    assert "<svg" in asset_response.text
    assert spa_fallback_response.status_code == 200
    assert "Kanban Studio" in spa_fallback_response.text
