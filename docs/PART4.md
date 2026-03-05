# Part 4 Frontend-Only Auth Notes

## What changed

- `frontend/src/app/page.tsx` now gates board access behind a login form.
- Hardcoded credentials:
  - username: `user`
  - password: `password`
- Auth state is stored in `sessionStorage` using key `kanban-authenticated`.
- On success, the app shows the Kanban board.
- A logout button in `KanbanBoard` clears the session key and returns to login.

## Test coverage added

- Unit:
  - `src/app/page.test.tsx` covers login required, invalid login, valid login/logout, and session restore.
  - Existing board unit tests continue to pass.
- Integration:
  - `tests/kanban.spec.ts` now logs in before board interactions.
  - Added integration case for invalid login + logout behavior.

## Manual checks

- Visit `/` and confirm login screen appears first.
- Attempt wrong credentials and confirm board remains hidden.
- Login with `user` / `password` and confirm board appears.
- Click `Log out` and confirm return to login screen.
