import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.board_store import validate_board_data


class AIResponseValidationError(ValueError):
    pass


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("conversation message content must be non-empty")
        return normalized


class AIChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str
    conversationHistory: list[ConversationMessage] = Field(default_factory=list)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("prompt must be non-empty")
        return normalized


class StructuredAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    board: dict[str, Any] | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message must be non-empty")
        return normalized


def build_ai_messages(
    board: dict[str, Any],
    prompt: str,
    conversation_history: list[ConversationMessage],
) -> list[dict[str, str]]:
    system_message = {
        "role": "system",
        "content": (
            "You are an assistant for a Kanban project management app. "
            "Always return ONLY a JSON object with exactly these keys: "
            "'message' (string) and 'board' (object or null). "
            "If no board update is needed, set 'board' to null. "
            "Do not include markdown, code fences, or extra keys."
        ),
    }
    messages: list[dict[str, str]] = [system_message]
    for message in conversation_history:
        messages.append({"role": message.role, "content": message.content})

    board_json = json.dumps(board, separators=(",", ":"), ensure_ascii=True)
    user_message = {
        "role": "user",
        "content": (
            "Current board JSON:\n"
            f"{board_json}\n\n"
            "User prompt:\n"
            f"{prompt}\n\n"
            "Return strictly valid JSON with keys 'message' and 'board'."
        ),
    }
    messages.append(user_message)
    return messages


def parse_structured_ai_response(raw_content: str) -> StructuredAIResponse:
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise AIResponseValidationError("AI response must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise AIResponseValidationError("AI response must be a JSON object")

    try:
        structured = StructuredAIResponse.model_validate(parsed)
    except Exception as exc:
        raise AIResponseValidationError(
            "AI response must include only 'message' and optional 'board'"
        ) from exc

    if structured.board is not None:
        try:
            validate_board_data(structured.board)
        except ValueError as exc:
            raise AIResponseValidationError(f"AI response board is invalid: {exc}") from exc

    return structured
