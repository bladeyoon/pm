# Backend Scaffold

## Run locally

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

When a static frontend export exists, set `FRONTEND_STATIC_DIR` to serve it:

```bash
FRONTEND_STATIC_DIR=../frontend/out python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Optional DB override:

```bash
DB_PATH=./data/local.sqlite3 python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## API endpoints

- `GET /api/health`
- `GET /api/board/{username}`
- `PUT /api/board/{username}`

## Run tests

```bash
pytest
```
