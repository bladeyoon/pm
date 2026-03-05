# Part 5 Database Modeling Proposal

This document proposes the SQLite data model for MVP persistence and defines the JSON contract for storing a user's Kanban board.

## Goals

- Support multiple users in the database design.
- Keep MVP implementation simple.
- Store one board per user.
- Store board state as serialized JSON in SQLite.
- Keep schema easy to migrate in later phases.

## Proposed SQLite Schema (V1)

### Table: `users`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `username` TEXT NOT NULL UNIQUE
- `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

### Table: `board_state`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL UNIQUE
- `board_json` TEXT NOT NULL CHECK (json_valid(board_json))
- `schema_version` INTEGER NOT NULL DEFAULT 1
- `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE

## SQL DDL (Reference)

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS board_state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  schema_version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## Board JSON Contract (V1)

The serialized `board_json` payload mirrors current frontend board types.

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    }
  }
}
```

### Validation Rules

- Top-level object must include `columns` and `cards`.
- `columns` is an array of objects with:
  - `id` (string, non-empty)
  - `title` (string, non-empty)
  - `cardIds` (array of strings)
- `cards` is an object keyed by card id.
- Each card object includes:
  - `id` (string, non-empty)
  - `title` (string, non-empty)
  - `details` (string, can be empty)
- Every id in `cardIds` must exist in `cards`.
- Every card should appear in exactly one column's `cardIds`.

## Why JSON Blob Storage for MVP

- Minimal schema complexity for rapid delivery.
- Matches current frontend data structure directly.
- Simple read/write path for full-board persistence.
- Easier to evolve API behavior before fine-grained relational normalization.

## Trade-Offs

- Pros:
  - Simple CRUD and low implementation overhead.
  - Fewer joins and fewer migration steps in MVP.
- Cons:
  - Harder to query individual cards efficiently.
  - Coarser update granularity (typically write full board JSON).
  - Future analytics/reporting likely need normalized tables.

## Migration Approach

- Keep `schema_version` in `board_state` to support payload upgrades.
- In Part 6/7:
  - Initialize DB if missing.
  - Seed default user and board row if absent.
  - Validate JSON before writes.
- Future (post-MVP) migration option:
  - Introduce normalized `boards`, `columns`, `cards`, and `board_events` tables.
  - Migrate from `board_json` to normalized rows in a one-time migration script.

## Planned Tests for Part 6

- Unit:
  - serialize/deserialize board JSON without data loss.
  - reject invalid JSON payloads.
  - enforce one-board-per-user uniqueness.
- Integration:
  - round-trip persistence: write board JSON, read back, assert equality.
  - DB bootstrap: create database + tables when missing.

## Sign-Off Request

Please confirm this Part 5 proposal so I can implement it in Part 6 exactly as written.
