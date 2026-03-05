# Part 10 Sidebar AI Chat + Live Board Refresh

## What changed

- Added sidebar AI chat UI to `frontend/src/components/KanbanBoard.tsx`.
- Wired chat requests to backend route `POST /api/ai/chat/{username}`.
- Added chat state handling for conversation history, loading, success, and error.
- Added automatic board refresh after accepted AI mutation.

## UI behavior

- New right-side panel: **AI Assistant / Board Chat**.
- Users can submit prompts from a textarea.
- Chat transcript displays:
  - user prompts,
  - assistant replies,
  - pending indicator (`Thinking...`) while request is in flight.
- Error banner appears when AI request fails or payload is invalid.

## Backend request path

Frontend sends:

```json
{
  "prompt": "User text",
  "conversationHistory": [
    { "role": "user", "content": "Previous user message" },
    { "role": "assistant", "content": "Previous assistant message" }
  ]
}
```

Notes:

- `conversationHistory` is built from prior chat messages only.
- Current user prompt is sent as `prompt`.

## Mutation + live refresh flow

- If backend returns `boardUpdated: true`:
  - frontend applies returned `board` immediately when present,
  - frontend then requests `GET /api/board/{username}` with `cache: "no-store"` to refresh from persisted source.
- If refresh fails after mutation, a board-sync warning is shown.

## Tests

- Unit:
  - `frontend/src/components/KanbanBoard.chat.test.tsx`
    - assistant response without mutation
    - response with mutation updates board and triggers refresh
    - invalid payload path shows error
- Integration/E2E:
  - `frontend/tests/kanban.spec.ts`
    - assistant response without mutation
    - response with mutation updates visible board
    - invalid payload path shows error banner
    - API responses mocked via Playwright route handlers for deterministic behavior

## Verification

- Unit tests:
  - `npm run test:unit`
  - Result: 16 passed
- Coverage:
  - `npx vitest run --coverage`
  - Result: 82.18% total frontend statements
- E2E:
  - `npm run test:e2e`
  - Result: 7 passed, 2 skipped (full-stack-only persistence tests skipped without `E2E_BASE_URL`)
