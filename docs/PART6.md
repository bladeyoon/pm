# Part 6 Backend API + SQLite Implementation

## What was implemented

- SQLite initialization and persistence layer in `backend/app/board_store.py`.
- FastAPI board endpoints in `backend/app/main.py`.
- DB bootstrap now runs at app creation and creates DB/tables when missing.
- Default seed user (`user`) and default board seed row are created when absent.

## Database behavior

- DB file path:
  - from `DB_PATH` env when provided
  - otherwise default: `backend/data/pm_mvp.sqlite3`
- Tables created:
  - `users`
  - `board_state` with JSON validity check
- One board per user is enforced via `UNIQUE(user_id)` in `board_state`.

## API endpoints

- `GET /api/health`
  - Returns service health.

- `GET /api/board/{username}`
  - Returns board for the given user.
  - If user does not exist, user + default board are created.

- `PUT /api/board/{username}`
  - Request body:

```json
{
  "board": {
    "columns": [],
    "cards": {}
  }
}
```

  - Validates board payload against Part 5 contract.
  - Persists validated board JSON for that user.
  - Returns updated board.

## Validation and errors

- Blank username returns `422`.
- Invalid board shape returns `422` with specific validation detail.
- Card IDs must exist in `cards` and cannot appear in multiple columns.
- Card `id` values must match their object keys.

## Tests run

- Command:
  - `uv run --extra dev pytest --cov=app --cov-report=term-missing`
- Result:
  - 9 tests passed
  - 88% total backend coverage
- Coverage includes:
  - DB bootstrap and seed creation
  - unknown user auto-creation
  - board round-trip persistence
  - invalid payload and username rejection
  - existing static frontend serving behavior
