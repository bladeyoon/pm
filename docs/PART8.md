# Part 8 OpenRouter Connectivity

## What changed

- Added backend OpenRouter client in `backend/app/openrouter_client.py`.
- Added connectivity endpoint `POST /api/ai/connectivity` in `backend/app/main.py`.
- Added Docker environment wiring for `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in `docker-compose.yml`.

## OpenRouter configuration

- `OPENROUTER_API_KEY`
  - Required only when calling AI connectivity route.
  - If missing, request fails and backend logs an error.
- `OPENROUTER_MODEL`
  - Optional.
  - Defaults to `openrouter/free` when not provided.

## Connectivity endpoint

- Route: `POST /api/ai/connectivity`
- Behavior:
  - Executes a hardcoded prompt `"2+2"` against OpenRouter.
  - Returns:

```json
{
  "status": "ok",
  "model": "openrouter/free",
  "prompt": "2+2",
  "response": "4"
}
```

- Error cases:
  - Missing API key: `500` with detail `OPENROUTER_API_KEY is not set` and backend log entry.
  - Provider/network failures: `502` with provider failure detail and backend log entry.

## Tests

- Unit:
  - `backend/tests/test_openrouter_client.py`
    - env-based model resolution
    - missing API key failure
    - successful response parsing
    - HTTP/network/provider-shape failure paths
- Integration-style API tests:
  - `backend/tests/test_main.py`
    - connectivity success response through API
    - connectivity provider error mapped to `502`

## Troubleshooting

- If connectivity returns `500`:
  - Verify root `.env` contains `OPENROUTER_API_KEY=...`.
  - Recreate container after env changes:
    - `docker compose up -d --build`
- If connectivity returns `502`:
  - Check backend logs:
    - `docker compose logs app`
  - Confirm outbound internet access from Docker runtime.
  - Confirm selected model in `OPENROUTER_MODEL` is available.
