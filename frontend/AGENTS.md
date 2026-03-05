# Frontend Codebase Guide

This document describes the current Kanban frontend implementation in `frontend/`.

## Purpose

- Provide a baseline description of the existing UI before API integration.
- Help future agents modify the code safely and consistently.

## Stack and Tooling

- Framework: Next.js App Router (`next` 16).
- Build target: static export (`output: "export"` in `next.config.ts`).
- Language: TypeScript + React 19.
- Styling: Tailwind CSS v4 + CSS variables in `src/app/globals.css`.
- Drag and drop: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`.
- Unit testing: Vitest + Testing Library (JSDOM).
- E2E testing: Playwright.

## Current App Behavior

- The home route (`src/app/page.tsx`) renders a frontend-only auth gate.
- Users must sign in with hardcoded credentials:
  - username: `user`
  - password: `password`
- Auth state is stored in `sessionStorage` (key: `kanban-authenticated`) and lasts for the browser session.
- After sign-in, users see `KanbanBoard` with a logout control.
- Board is client-side and in-memory (no backend persistence yet).
- The static build output is served by FastAPI in Docker (Part 3), but board state is still browser-local.
- Authenticated users can:
  - Rename fixed columns.
  - Drag and drop cards within and across columns.
  - Add a card to a column.
  - Delete a card.
- Logging out clears session auth and returns to the sign-in screen.

## Key Files

- `src/app/page.tsx`:
  - Handles login form, credential check, session persistence, and logout.
  - Renders `KanbanBoard` only after successful auth.
- `src/components/KanbanBoard.tsx`:
  - Holds board state (`BoardData`) in React state.
  - Handles drag start/end and card movement.
  - Handles column rename, add card, delete card.
- `src/components/KanbanColumn.tsx`:
  - Renders one column with editable title.
  - Provides droppable area and sortable card list.
  - Hosts `NewCardForm`.
- `src/components/KanbanCard.tsx`:
  - Sortable draggable card component.
  - Delete action trigger.
- `src/components/NewCardForm.tsx`:
  - Expandable form for adding a new card.
  - Requires non-empty title.
- `src/lib/kanban.ts`:
  - Core types: `Card`, `Column`, `BoardData`.
  - `initialData` seed board.
  - `moveCard` utility for reorder/move logic.
  - `createId` helper for new card IDs.

## Styling and Theme

- Global color variables are defined in `src/app/globals.css`.
- Existing palette aligns with project-level colors in root `AGENTS.md`.
- Layout uses large dashboard-style cards and responsive grid.

## Current Tests

- Unit:
  - `src/lib/kanban.test.ts`: `moveCard` behavior.
  - `src/components/KanbanBoard.test.tsx`: render, rename, add/remove card flows.
  - `src/app/page.test.tsx`: login failure/success, session restore, logout flow.
  - `src/components/KanbanCardPreview.test.tsx`: preview content rendering.
- Integration/E2E:
  - `tests/kanban.spec.ts`: login flows plus board load/add/move interactions.
- Test tooling config:
  - `vitest.config.ts`
  - `playwright.config.ts`
  - `src/test/setup.ts`

## Commands

- Install: `npm install`
- Dev server: `npm run dev`
- Build: `npm run build`
- Unit tests: `npm run test:unit`
- E2E tests: `npm run test:e2e`
- All tests: `npm run test:all`
- Lint: `npm run lint`

## Known Limitations (Current State)

- No backend API integration for board data; state resets on refresh.
- No AI chat sidebar.
- No database persistence.

## Change Guidance for Future Parts

- Keep component boundaries simple; prefer small focused updates.
- Preserve existing data-testid attributes used by tests unless tests are updated together.
- When changing board behavior, update both unit tests and E2E coverage.
- Avoid adding features not explicitly requested by the current phase plan.
