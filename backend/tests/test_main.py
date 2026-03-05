from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.board_store import DEFAULT_BOARD
from app.main import HELLO_PAGE, create_app, resolve_frontend_asset
from app.openrouter_client import OpenRouterRequestError


class StubAIClient:
    def __init__(
        self,
        model: str,
        response: str | None = None,
        error: Exception | None = None,
        chat_response: str | None = None,
        chat_error: Exception | None = None,
    ) -> None:
        self.model = model
        self._response = response
        self._error = error
        self._chat_response = chat_response
        self._chat_error = chat_error
        self.last_messages: list[dict[str, str]] = []

    def smoke_check(self) -> str:
        if self._error is not None:
            raise self._error
        if self._response is None:
            raise RuntimeError("stub response missing")
        return self._response

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.last_messages = messages
        if self._chat_error is not None:
            raise self._chat_error
        if self._chat_response is None:
            raise RuntimeError("stub chat response missing")
        return self._chat_response


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


def test_ai_connectivity_returns_smoke_result(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            frontend_dir=None,
            db_path=tmp_path / "pm.sqlite3",
            ai_client=StubAIClient(model="openrouter/free", response="4"),
        )
    )

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model": "openrouter/free",
        "prompt": "2+2",
        "response": "4",
    }


def test_ai_connectivity_maps_provider_failure_to_502(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            frontend_dir=None,
            db_path=tmp_path / "pm.sqlite3",
            ai_client=StubAIClient(
                model="openrouter/free",
                error=OpenRouterRequestError("provider request failed"),
            ),
        )
    )

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 502
    assert response.json()["detail"] == "provider request failed"


def test_ai_connectivity_missing_api_key_returns_500_and_logs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = TestClient(create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3"))

    with caplog.at_level("ERROR"):
        response = client.post("/api/ai/connectivity")

    assert response.status_code == 500
    assert response.json()["detail"] == "OPENROUTER_API_KEY is not set"
    assert "OpenRouter connectivity failed due to missing config" in caplog.text


def test_ai_chat_returns_message_without_board_update(tmp_path: Path) -> None:
    stub_ai_client = StubAIClient(
        model="openrouter/free",
        chat_response='{"message":"No board update needed.","board":null}',
    )
    client = TestClient(
        create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3", ai_client=stub_ai_client)
    )

    response = client.post(
        "/api/ai/chat/user",
        json={
            "prompt": "Summarize my board",
            "conversationHistory": [{"role": "user", "content": "Can you help me?"}],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model": "openrouter/free",
        "reply": "No board update needed.",
        "boardUpdated": False,
        "board": None,
    }
    assert len(stub_ai_client.last_messages) == 3
    assert "Current board JSON:" in stub_ai_client.last_messages[-1]["content"]
    assert "User prompt:" in stub_ai_client.last_messages[-1]["content"]


def test_ai_chat_applies_valid_board_mutation(tmp_path: Path) -> None:
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
    stub_ai_client = StubAIClient(
        model="openrouter/free",
        chat_response='{"message":"Applied your requested update.","board":{"columns":[{"id":"col-1","title":"Todo","cardIds":["card-1"]}],"cards":{"card-1":{"id":"card-1","title":"Write API tests","details":"Ensure put/get round-trip works."}}}}',
    )
    client = TestClient(
        create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3", ai_client=stub_ai_client)
    )

    chat_response = client.post(
        "/api/ai/chat/user",
        json={"prompt": "Create one todo card named Write API tests", "conversationHistory": []},
    )
    board_response = client.get("/api/board/user")

    assert chat_response.status_code == 200
    assert chat_response.json() == {
        "status": "ok",
        "model": "openrouter/free",
        "reply": "Applied your requested update.",
        "boardUpdated": True,
        "board": updated_board,
    }
    assert board_response.status_code == 200
    assert board_response.json()["board"] == updated_board


def test_ai_chat_rejects_invalid_ai_schema_response(tmp_path: Path) -> None:
    stub_ai_client = StubAIClient(
        model="openrouter/free",
        chat_response='{"reply":"wrong field","board":null}',
    )
    client = TestClient(
        create_app(frontend_dir=None, db_path=tmp_path / "pm.sqlite3", ai_client=stub_ai_client)
    )

    response = client.post(
        "/api/ai/chat/user",
        json={"prompt": "Summarize board", "conversationHistory": []},
    )

    assert response.status_code == 502
    assert "must include only 'message' and optional 'board'" in response.json()["detail"]


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
