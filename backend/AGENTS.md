## Backend Overview

The backend is now scaffolded as a FastAPI service under `backend/`.

### Current implementation

- App entrypoint: `backend/app/main.py`
- Endpoints:
  - `GET /` serves the built frontend app when static output exists; otherwise returns the hello-world fallback page.
  - `GET /api/health` returns JSON health data.
- Non-API routes (`/{path}`) serve exported frontend assets and use SPA fallback to `index.html`.
- Static directory is configured via `FRONTEND_STATIC_DIR` (set in Docker to `/app/frontend-static`).

### Tests

- Unit/API tests are in `backend/tests/test_main.py`.
- Tests verify:
  - Root route behavior for fallback and static frontend modes.
  - Static asset path resolution and traversal protection.
  - Health endpoint returns expected JSON payload.

### Runtime

- Local run command: `uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`
- Container run is managed from repo root using `docker compose`.