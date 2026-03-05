import os
from pathlib import Path
from typing import Any
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, ConfigDict
from starlette.responses import Response
from app.ai_chat import (
    AIChatRequest,
    AIResponseValidationError,
    build_ai_messages,
    parse_structured_ai_response,
)
from app.board_store import (
    get_board_for_user,
    initialize_database,
    resolve_db_path,
    update_board_for_user,
)
from app.openrouter_client import OpenRouterClient, OpenRouterConfigError, OpenRouterRequestError

logger = logging.getLogger(__name__)

HELLO_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Project Management MVP</title>
    <style>
      body {
        font-family: "Segoe UI", sans-serif;
        margin: 0;
        background: #f7f8fb;
        color: #032147;
      }
      main {
        max-width: 720px;
        margin: 80px auto;
        padding: 24px;
        background: #ffffff;
        border: 1px solid rgba(3, 33, 71, 0.08);
        border-radius: 16px;
      }
      h1 {
        margin-top: 0;
      }
      button {
        background: #753991;
        color: #ffffff;
        border: 0;
        border-radius: 999px;
        padding: 10px 16px;
        cursor: pointer;
      }
      pre {
        margin-top: 16px;
        padding: 12px;
        background: #f7f8fb;
        border-radius: 8px;
        border: 1px solid rgba(3, 33, 71, 0.08);
        overflow-x: auto;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Hello from FastAPI</h1>
      <p>This scaffold confirms static HTML is served at <code>/</code>.</p>
      <button id="health-button" type="button">Call /api/health</button>
      <pre id="health-output">Not called yet.</pre>
    </main>
    <script>
      const button = document.getElementById("health-button");
      const output = document.getElementById("health-output");

      button.addEventListener("click", async () => {
        output.textContent = "Loading...";
        try {
          const response = await fetch("/api/health");
          const payload = await response.json();
          output.textContent = JSON.stringify(payload, null, 2);
        } catch (error) {
          output.textContent = `Request failed: ${error}`;
        }
      });
    </script>
  </body>
</html>
"""


def resolve_frontend_dir() -> Path | None:
    env_path = os.getenv("FRONTEND_STATIC_DIR")
    if env_path:
        candidate = Path(env_path)
    else:
        candidate = Path(__file__).resolve().parents[2] / "frontend" / "out"
    index_file = candidate / "index.html"
    if index_file.is_file():
        return candidate
    return None


def resolve_frontend_asset(frontend_dir: Path, request_path: str) -> Path | None:
    normalized = request_path.lstrip("/")
    if not normalized:
        return frontend_dir / "index.html"

    candidate = (frontend_dir / normalized).resolve()
    if frontend_dir.resolve() not in candidate.parents and candidate != frontend_dir.resolve():
        return None
    if candidate.is_file():
        return candidate
    return None


class BoardResponse(BaseModel):
    username: str
    board: dict[str, Any]
    schemaVersion: int = 1


class BoardUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    board: dict[str, Any]


class AIConnectivityResponse(BaseModel):
    status: str
    model: str
    prompt: str
    response: str


class AIChatResponse(BaseModel):
    status: str
    model: str
    reply: str
    boardUpdated: bool
    board: dict[str, Any] | None = None


def create_app(
    frontend_dir: Path | None = None,
    db_path: Path | None = None,
    ai_client: OpenRouterClient | None = None,
) -> FastAPI:
    app = FastAPI(title="Project Management MVP API")
    resolved_frontend_dir = frontend_dir if frontend_dir is not None else resolve_frontend_dir()
    resolved_db_path = db_path if db_path is not None else resolve_db_path()
    resolved_ai_client = ai_client if ai_client is not None else OpenRouterClient.from_env()
    initialize_database(resolved_db_path)

    @app.get("/api/health")
    def read_health() -> dict[str, str]:
        return {"status": "ok", "service": "pm-mvp-backend"}

    @app.get("/api/board/{username}", response_model=BoardResponse)
    def read_board(username: str) -> BoardResponse:
        try:
            board = get_board_for_user(resolved_db_path, username)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return BoardResponse(username=username, board=board)

    @app.put("/api/board/{username}", response_model=BoardResponse)
    def write_board(username: str, payload: BoardUpdateRequest) -> BoardResponse:
        try:
            updated_board = update_board_for_user(resolved_db_path, username, payload.board)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return BoardResponse(username=username, board=updated_board)

    @app.post("/api/ai/connectivity", response_model=AIConnectivityResponse)
    def post_ai_connectivity_check() -> AIConnectivityResponse:
        prompt = "2+2"
        try:
            response_text = resolved_ai_client.smoke_check()
        except OpenRouterConfigError as exc:
            logger.error("OpenRouter connectivity failed due to missing config: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except OpenRouterRequestError as exc:
            logger.error("OpenRouter connectivity request failed: %s", exc)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return AIConnectivityResponse(
            status="ok",
            model=resolved_ai_client.model,
            prompt=prompt,
            response=response_text,
        )

    @app.post("/api/ai/chat/{username}", response_model=AIChatResponse)
    def post_ai_chat(username: str, payload: AIChatRequest) -> AIChatResponse:
        try:
            current_board = get_board_for_user(resolved_db_path, username)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        ai_messages = build_ai_messages(current_board, payload.prompt, payload.conversationHistory)
        try:
            raw_response = resolved_ai_client.chat(ai_messages)
        except OpenRouterConfigError as exc:
            logger.error("OpenRouter AI chat failed due to missing config: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except OpenRouterRequestError as exc:
            logger.error("OpenRouter AI chat request failed: %s", exc)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        try:
            structured = parse_structured_ai_response(raw_response)
        except AIResponseValidationError as exc:
            logger.error("OpenRouter AI chat returned invalid schema: %s", exc)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        if structured.board is None:
            return AIChatResponse(
                status="ok",
                model=resolved_ai_client.model,
                reply=structured.message,
                boardUpdated=False,
            )

        updated_board = update_board_for_user(resolved_db_path, username, structured.board)
        return AIChatResponse(
            status="ok",
            model=resolved_ai_client.model,
            reply=structured.message,
            boardUpdated=True,
            board=updated_board,
        )

    @app.get("/", response_class=HTMLResponse)
    def read_root() -> Response:
        if resolved_frontend_dir is not None:
            return FileResponse(resolved_frontend_dir / "index.html")
        return HTMLResponse(content=HELLO_PAGE)

    @app.get("/{full_path:path}")
    def serve_frontend_or_404(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        if resolved_frontend_dir is None:
            raise HTTPException(status_code=404, detail="Not found")
        asset = resolve_frontend_asset(resolved_frontend_dir, full_path)
        if asset is not None:
            return FileResponse(asset)
        return FileResponse(resolved_frontend_dir / "index.html")

    return app


app = create_app()
