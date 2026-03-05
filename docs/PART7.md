# Part 7 Frontend + Backend Persistence

## What changed

- Frontend now loads board state from backend after login.
- Board updates (rename, add, move, delete) are saved to backend API.
- Session restores still work and now use persisted board data.
- Minimal loading/error UI is shown for board load/save failures.

## Frontend updates

- `frontend/src/components/KanbanBoard.tsx`
  - Added `username` prop.
  - Fetches `GET /api/board/{username}` on mount when username exists.
  - Sends `PUT /api/board/{username}` after board mutations.
  - Shows:
    - loading state: "Loading board..."
    - save/load error banner when API calls fail

- `frontend/src/app/page.tsx`
  - Stores authenticated username in session (`kanban-username`).
  - Passes username into `KanbanBoard`.

## Tests

- Unit:
  - `src/components/KanbanBoard.persistence.test.tsx`
    - verifies initial board fetch from API
    - verifies PUT persistence on board changes
  - updated `src/app/page.test.tsx` for async board load with mocked fetch
- Integration:
  - updated `frontend/tests/kanban.spec.ts`
  - added persistence test that verifies a new card remains after page reload
  - ran Playwright against containerized app using:
    - `E2E_BASE_URL=http://127.0.0.1:8010 npm run test:e2e`

## Verification results

- Unit tests: passed
- Frontend coverage: 80.86%
- E2E against full stack (backend + static frontend): 5 passed

## Developer note

`frontend/playwright.config.ts` now supports `E2E_BASE_URL`.
- If set, Playwright tests run against that URL and do not start Next dev server.
- If not set, existing local dev-server behavior is preserved.
