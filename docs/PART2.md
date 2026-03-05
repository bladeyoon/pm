# Part 2 Scaffolding Notes

## What is scaffolded

- FastAPI backend in `backend/`.
- Docker image at repo root via `Dockerfile`.
- Container orchestration with `docker-compose.yml`.
- OS start/stop scripts in `scripts/`.

## Start and stop

- macOS:
  - Start: `./scripts/start-mac.sh`
  - Stop: `./scripts/stop-mac.sh`
- Linux:
  - Start: `./scripts/start-linux.sh`
  - Stop: `./scripts/stop-linux.sh`
- Windows:
  - Start: `scripts\start-windows.bat`
  - Stop: `scripts\stop-windows.bat`

Default host port is `8010` to reduce local conflicts.
Set `APP_PORT` to override (for example `APP_PORT=8000`).

## Verification

- `GET /` should return a hello-world HTML page.
- `GET /api/health` should return:

```json
{"status":"ok","service":"pm-mvp-backend"}
```

- The root page has a button that calls `/api/health` and prints the JSON response.
