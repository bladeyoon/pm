# Part 9 Structured AI Output + Optional Board Mutation

## What changed

- Added structured AI chat module in `backend/app/ai_chat.py`.
- Added backend route `POST /api/ai/chat/{username}` in `backend/app/main.py`.
- Extended OpenRouter client with message-based chat support in `backend/app/openrouter_client.py`.

## Request contract (frontend to backend)

Route:

- `POST /api/ai/chat/{username}`

Body:

```json
{
  "prompt": "Move one card from backlog to in progress",
  "conversationHistory": [
    { "role": "user", "content": "Help me clean this board." },
    { "role": "assistant", "content": "Sure, what should be changed?" }
  ]
}
```

Notes:

- `prompt` is required and must be non-empty.
- `conversationHistory` is optional and defaults to `[]`.
- `conversationHistory.role` must be `user` or `assistant`.

## AI response schema (strict)

The backend requires the model to return **JSON only** with exactly these keys:

```json
{
  "message": "Human-friendly reply text",
  "board": null
}
```

or:

```json
{
  "message": "Updated your board.",
  "board": {
    "columns": [],
    "cards": {}
  }
}
```

Rules:

- No markdown/code fences.
- No extra keys.
- `message` must be a non-empty string.
- `board` must be either:
  - `null`, or
  - a full board object that passes existing board validation rules.

## Backend behavior

- Backend loads current board for `{username}`.
- Backend sends OpenRouter a message package containing:
  - system instruction for strict JSON schema,
  - prior conversation history,
  - current board JSON,
  - user prompt.
- Backend parses/validates AI JSON response.
- If `board` is `null`:
  - returns assistant `message` only.
- If `board` is provided and valid:
  - persists the board via existing board update path,
  - returns `boardUpdated: true` and updated board payload.
- Invalid AI schema or invalid AI board payload is rejected with `502`.

## Endpoint response

```json
{
  "status": "ok",
  "model": "openrouter/free",
  "reply": "Updated your board.",
  "boardUpdated": true,
  "board": {
    "columns": [],
    "cards": {}
  }
}
```

When no board update is applied:

```json
{
  "status": "ok",
  "model": "openrouter/free",
  "reply": "No update needed.",
  "boardUpdated": false,
  "board": null
}
```

## Tests

- Unit:
  - `backend/tests/test_ai_chat.py`
    - schema validator valid/invalid cases
    - conversation packaging checks (board + prompt + history)
- Integration-style API:
  - `backend/tests/test_main.py`
    - valid response only (no mutation)
    - valid response + board mutation (persists)
    - invalid AI schema response rejected

## Verification

- Command:
  - `uv run --extra dev pytest --cov=app --cov-report=term-missing`
- Result:
  - 27 tests passed
  - 88% backend coverage
