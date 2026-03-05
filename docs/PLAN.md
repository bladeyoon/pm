# Project Implementation Plan

This document defines the execution plan for the MVP in `AGENTS.md`.

## Confirmed Constraints and Decisions

- Frontend: Next.js app in `frontend/`.
- Backend: Python FastAPI in `backend/`.
- Runtime: Local Docker container for full stack.
- Python package manager: `uv`.
- AI provider: OpenRouter using `OPENROUTER_API_KEY` in root `.env`.
- AI model target: `openrouter/free`.
- Data store: SQLite; Kanban state stored as serialized JSON in a column/blob.
- Auth for MVP:
  - Initial sign-in UX in frontend only (hardcoded `user` / `password`).
  - Backend auth added later.
- Testing quality bar:
  - Minimum 80% unit test coverage for implemented backend/frontend units in each completed phase.
  - Robust integration testing for cross-component or cross-service behavior.
- Runtime/testing decisions from completed phases:
  - Default Docker host port is `8010` (override with `APP_PORT`).
  - Full-stack Playwright runs use `E2E_BASE_URL` to target containerized app.
  - Frontend persistence flow waits for pending save before logout and uses `cache: "no-store"` on board API requests.
- Approval gate: complete planning artifacts first, then wait for user approval before coding phases.

## Global Definition of Done

- [ ] Feature behavior matches the corresponding part requirements only (no extra features).
- [ ] Unit tests added/updated and passing with at least 80% coverage for changed units.
- [ ] Integration tests added/updated and passing for key user flows.
- [ ] Root cause identified and fixed for any issue encountered; no speculative fixes.
- [ ] Documentation updated for behavior, setup, and test execution changes.
- [ ] Manual sanity check performed for modified flow.

## Part 1 - Planning and Baseline Documentation

### Checklist

- [x] Expand `docs/PLAN.md` into executable, testable phased plan (this file).
- [x] Create `frontend/AGENTS.md` describing current frontend architecture and behavior.
- [x] Confirm acceptance criteria, risks, and test strategy per part.
- [x] Obtain user sign-off on plan before beginning Part 2.

### Tests

- N/A (documentation-only part).

### Success Criteria

- [x] User confirms this plan and approves transition to implementation.

## Part 2 - Scaffolding (Docker + FastAPI + Scripts)

### Checklist

- [x] Create backend scaffold in `backend/` with FastAPI app entrypoint.
- [x] Add containerization files for backend runtime now, ready to extend for frontend static serving in Part 3.
- [x] Add start/stop scripts for Mac/Windows/Linux under `scripts/`.
- [x] Add "hello world" static response served at `/` from backend scaffold stage.
- [x] Add at least one example API route (e.g., `/api/health`) and wire it in container runtime.
- [x] Document how to build, start, stop, and verify the scaffold.

### Tests

- Unit:
  - [x] Backend route tests for `/` and `/api/health`.
- Integration:
  - [x] Container-level test proving app boots and both static root + API endpoint respond.
- Coverage:
  - [x] Verify backend unit coverage meets or exceeds 80%.

### Success Criteria

- [x] `docker` workflow starts cleanly.
- [x] `GET /` returns expected hello-world scaffold page.
- [x] `GET /api/health` returns expected success payload.
- [x] Start/stop scripts work on their target OS conventions.

## Part 3 - Serve Existing Frontend from Backend

### Checklist

- [x] Build frontend statically from `frontend/`.
- [x] Configure backend/container to serve built frontend at `/`.
- [x] Ensure demo Kanban board renders correctly with existing interactions.
- [x] Update docs with static build/serve flow.

### Tests

- Unit:
  - [x] Maintain/update frontend unit tests for board operations.
  - [x] Add backend unit test coverage for static asset serving path logic.
- Integration:
  - [x] End-to-end test that `/` loads Kanban UI from backend-served static assets.
- Coverage:
  - [x] Frontend changed units >= 80%; backend changed units >= 80%.

### Success Criteria

- [x] Visiting `/` in containerized app displays Kanban Studio UI (not scaffold page).
- [x] Static assets load without broken routes.
- [x] Existing board interactions continue to work.

## Part 4 - Frontend-Only Fake Sign-In

### Checklist

- [x] Add login screen on first visit.
- [x] Validate hardcoded credentials in frontend (`user` / `password`).
- [x] Persist session state client-side for current browser session.
- [x] Add logout control returning to login screen.
- [x] Ensure unauthorized users cannot see board until login in current UX.

### Tests

- Unit:
  - [x] Form validation, credential check, session state transitions.
- Integration:
  - [x] Login success flow shows board.
  - [x] Login failure keeps user on login screen.
  - [x] Logout returns user to login screen and hides board.
- Coverage:
  - [x] Frontend changed units >= 80%.

### Success Criteria

- [x] App gates board behind login UI.
- [x] Valid credentials unlock board.
- [x] Logout reliably resets visible session state.

## Part 5 - Database Modeling and Design Sign-Off

### Checklist

- [x] Define SQLite schema for users + board storage.
- [x] Store board data as serialized JSON in SQLite column/blob.
- [x] Document schema decisions, trade-offs, and migration approach in `docs/`.
- [x] Define JSON payload structure for board persistence.
- [x] Request and obtain user approval before implementing data access layer.

### Tests

- Unit:
  - [x] Schema serialization/deserialization tests for board JSON.
- Integration:
  - [x] Round-trip test: save board JSON, read board JSON, verify equality.
- Coverage:
  - [x] Backend changed units >= 80%.

### Success Criteria

- [x] Schema documented and approved by user.
- [x] JSON persistence contract is explicit and test-backed.

## Part 6 - Backend Kanban API

### Checklist

- [x] Implement DB initialization if file does not exist.
- [x] Implement API routes for reading and updating board per user.
- [x] Add request/response models and validation.
- [x] Add error handling for invalid payloads and unknown users.
- [x] Document endpoints and local test usage.

### Tests

- Unit:
  - [x] DB layer tests (create, read, update, initialization path).
  - [x] API handler tests for valid and invalid requests.
- Integration:
  - [x] API-to-DB tests proving persisted state across requests.
- Coverage:
  - [x] Backend changed units >= 80%.

### Success Criteria

- [x] Backend can create DB automatically.
- [x] Board GET/UPDATE API operations work for target user.
- [x] Invalid requests return clear, consistent errors.

## Part 7 - Frontend Wired to Backend Persistence

### Checklist

- [x] Replace frontend in-memory board source with backend API integration.
- [x] Load board on login/session start.
- [x] Persist board changes (rename/move/add/delete) via API.
- [x] Handle loading, error, and retry states minimally and clearly.
- [x] Keep UX aligned with existing MVP styling.

### Tests

- Unit:
  - [x] Frontend API client and state transition tests.
- Integration:
  - [x] UI + backend persistence flow tests for key board operations.
  - [x] Refresh behavior test confirms persisted board reloads correctly.
  - [x] Logout/login flow confirms persisted board reloads correctly.
- Coverage:
  - [x] Frontend changed units >= 80%.

### Success Criteria

- [x] Board state persists across page reloads.
- [x] Core board operations update both UI and backend consistently.

## Part 8 - OpenRouter Connectivity

### Checklist

- [x] Implement backend AI client using OpenRouter configuration.
- [x] Read API key from environment and fail clearly when connectivity endpoint is called.
- [x] Add connectivity endpoint/path used for simple prompt validation.
- [x] Validate with "2+2" smoke call.
- [x] Document environment variables and troubleshooting steps.

### Tests

- Unit:
  - [x] AI client tests with mocked provider responses and failures.
- Integration:
  - [x] Connectivity test path using controlled test doubles.
  - [x] Manual smoke verification with real key for "2+2".
- Coverage:
  - [x] Backend changed units >= 80%.

### Success Criteria

- [x] Backend can successfully call OpenRouter.
- [x] Connectivity behavior is test-covered and documented.

## Part 9 - Structured Output With Optional Board Mutation

### Checklist

- [x] Define strict structured output schema in docs and code.
- [x] Include board JSON, user prompt, and conversation history in AI request.
- [x] Parse and validate AI response against strict schema.
- [x] Reject non-conforming AI responses in backend with explicit error handling.
- [x] Support optional board update payload plus user-facing text response.

### Tests

- Unit:
  - [x] Schema validator tests for valid/invalid response payloads.
  - [x] Conversation packaging tests.
- Integration:
  - [x] End-to-end backend flow test with mocked AI returning:
    - valid response only
    - valid response + board mutation
    - invalid schema response (must be rejected)
- Coverage:
  - [x] Backend changed units >= 80%.

### Success Criteria

- [x] AI responses are schema-validated reliably.
- [x] Non-conforming responses are rejected safely.
- [x] Valid board mutation payloads can be applied.

## Part 10 - Sidebar AI Chat UX + Live Board Refresh

### Checklist

- [ ] Add sidebar chat UI integrated into existing Kanban layout.
- [ ] Implement conversation history handling in UI and backend request path.
- [ ] Display assistant responses clearly with pending/error states.
- [ ] Apply AI-provided board mutation when present.
- [ ] Auto-refresh board state in UI after AI mutation is accepted.

### Tests

- Unit:
  - [ ] Chat UI state tests (send, loading, success, error).
  - [ ] Board mutation application tests.
- Integration:
  - [ ] End-to-end chat flow:
    - assistant response without mutation
    - assistant response with mutation updates board
    - invalid AI payload error path
- Coverage:
  - [ ] Frontend changed units >= 80%.

### Success Criteria

- [ ] Sidebar chat is usable and visually consistent with app styling.
- [ ] AI responses appear in chat.
- [ ] When AI mutation is provided and valid, board updates automatically.
- [ ] Failure paths are handled gracefully without corrupting board state.