## Backend Overview

The backend runs as a FastAPI service under `backend/`.

### Current implementation

- App entrypoint: `backend/app/main.py`
- Persistence module: `backend/app/board_store.py`
- Endpoints:
  - `GET /` serves the built frontend app when static output exists; otherwise returns the hello-world fallback page.
  - `GET /api/health` returns JSON health data.
  - `GET /api/board/{username}` returns a user's board, auto-creating user/default board when absent.
  - `PUT /api/board/{username}` validates and updates a user's board JSON.
  - `POST /api/ai/connectivity` performs a hardcoded `"2+2"` OpenRouter connectivity check.
- Non-API routes (`/{path}`) serve exported frontend assets and use SPA fallback to `index.html`.
- Static directory is configured via `FRONTEND_STATIC_DIR` (set in Docker to `/app/frontend-static`).
- Database path is configured with `DB_PATH` (default `backend/data/pm_mvp.sqlite3`).

### Tests

- Unit/API tests are in `backend/tests/test_main.py`.
- Tests verify:
  - Root route behavior for fallback and static frontend modes.
  - Static asset path resolution and traversal protection.
  - Health endpoint returns expected JSON payload.
  - DB bootstrap and default seed behavior.
  - Board read/write round-trip.
  - Invalid board payload and invalid username handling.
  - OpenRouter connectivity success/failure API behavior.
  - OpenRouter client parsing and provider error handling via mocks.

### Runtime

- Local run command: `uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`
- Container run is managed from repo root using `docker compose`.