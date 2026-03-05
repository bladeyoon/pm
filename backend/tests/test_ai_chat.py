import json

import pytest

from app.ai_chat import (
    AIResponseValidationError,
    ConversationMessage,
    build_ai_messages,
    parse_structured_ai_response,
)


def test_build_ai_messages_includes_history_board_and_prompt() -> None:
    board = {
        "columns": [{"id": "col-1", "title": "Todo", "cardIds": ["card-1"]}],
        "cards": {"card-1": {"id": "card-1", "title": "Test", "details": "Test details"}},
    }
    history = [
        ConversationMessage(role="user", content="Help me plan work."),
        ConversationMessage(role="assistant", content="Sure, what should we change?"),
    ]

    messages = build_ai_messages(board, "Move card-1 to done", history)

    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "Help me plan work."}
    assert messages[2] == {"role": "assistant", "content": "Sure, what should we change?"}
    assert messages[3]["role"] == "user"
    assert "Current board JSON:" in messages[3]["content"]
    assert "User prompt:" in messages[3]["content"]
    assert json.dumps(board, separators=(",", ":"), ensure_ascii=True) in messages[3]["content"]


def test_parse_structured_ai_response_accepts_message_only() -> None:
    parsed = parse_structured_ai_response('{"message":"No update needed.","board":null}')

    assert parsed.message == "No update needed."
    assert parsed.board is None


def test_parse_structured_ai_response_accepts_valid_board_mutation() -> None:
    raw = (
        '{"message":"Updated board.",'
        '"board":{"columns":[{"id":"col-1","title":"Todo","cardIds":["card-1"]}],'
        '"cards":{"card-1":{"id":"card-1","title":"Write tests","details":"Done"}}}}'
    )

    parsed = parse_structured_ai_response(raw)

    assert parsed.message == "Updated board."
    assert parsed.board is not None
    assert parsed.board["columns"][0]["id"] == "col-1"


def test_parse_structured_ai_response_rejects_non_json() -> None:
    with pytest.raises(AIResponseValidationError, match="must be valid JSON"):
        parse_structured_ai_response("not-json")


def test_parse_structured_ai_response_rejects_schema_mismatch() -> None:
    with pytest.raises(AIResponseValidationError, match="must include only 'message' and optional 'board'"):
        parse_structured_ai_response('{"reply":"wrong key","board":null}')


def test_parse_structured_ai_response_rejects_invalid_board_shape() -> None:
    invalid_board_payload = (
        '{"message":"Attempted update.",'
        '"board":{"columns":[{"id":"col-1","title":"Todo","cardIds":["missing-card"]}],"cards":{}}}'
    )

    with pytest.raises(AIResponseValidationError, match="board is invalid"):
        parse_structured_ai_response(invalid_board_payload)
