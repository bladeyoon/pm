# Part 3 Frontend Static Serving Notes

## What changed

- `frontend` now builds as a static export (`next.config.ts` sets `output: "export"`).
- `Dockerfile` uses a multi-stage build:
  - Node stage builds frontend into `frontend/out`.
  - Python stage copies build output to `/app/frontend-static`.
- FastAPI serves:
  - `/api/*` API routes as backend endpoints.
  - `/` and other non-API routes from static frontend files.
  - SPA fallback to `index.html` for client routes.

## Run and verify

- Start:
  - macOS: `./scripts/start-mac.sh`
  - Linux: `./scripts/start-linux.sh`
  - Windows: `scripts\start-windows.bat`
- Default URL: `http://127.0.0.1:8010`

Expected checks:

- `GET /` renders the Kanban app (contains "Kanban Studio").
- `GET /api/health` returns:

```json
{"status":"ok","service":"pm-mvp-backend"}
```

- A static asset path such as `/_next/static/...` returns `200`.
