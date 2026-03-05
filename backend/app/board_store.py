import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_BOARD: dict[str, Any] = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {
            "id": "card-1",
            "title": "Align roadmap themes",
            "details": "Draft quarterly themes with impact statements and metrics.",
        },
        "card-2": {
            "id": "card-2",
            "title": "Gather customer signals",
            "details": "Review support tags, sales notes, and churn feedback.",
        },
        "card-3": {
            "id": "card-3",
            "title": "Prototype analytics view",
            "details": "Sketch initial dashboard layout and key drill-downs.",
        },
        "card-4": {
            "id": "card-4",
            "title": "Refine status language",
            "details": "Standardize column labels and tone across the board.",
        },
        "card-5": {
            "id": "card-5",
            "title": "Design card layout",
            "details": "Add hierarchy and spacing for scanning dense lists.",
        },
        "card-6": {
            "id": "card-6",
            "title": "QA micro-interactions",
            "details": "Verify hover, focus, and loading states.",
        },
        "card-7": {
            "id": "card-7",
            "title": "Ship marketing page",
            "details": "Final copy approved and asset pack delivered.",
        },
        "card-8": {
            "id": "card-8",
            "title": "Close onboarding sprint",
            "details": "Document release notes and share internally.",
        },
    },
}


def resolve_db_path() -> Path:
    env_path = os.getenv("DB_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parents[1] / "data" / "pm_mvp.sqlite3"


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _normalize_username(username: str) -> str:
    normalized = username.strip()
    if not normalized:
        raise ValueError("username must be non-empty")
    return normalized


def validate_board_data(board: Any) -> None:
    if not isinstance(board, dict):
        raise ValueError("board must be an object")

    columns = board.get("columns")
    cards = board.get("cards")

    if not isinstance(columns, list):
        raise ValueError("columns must be an array")
    if not isinstance(cards, dict):
        raise ValueError("cards must be an object")

    cards_seen_in_columns: set[str] = set()
    for column in columns:
        if not isinstance(column, dict):
            raise ValueError("column entries must be objects")
        if not isinstance(column.get("id"), str) or not column["id"].strip():
            raise ValueError("column id must be a non-empty string")
        if not isinstance(column.get("title"), str) or not column["title"].strip():
            raise ValueError("column title must be a non-empty string")
        card_ids = column.get("cardIds")
        if not isinstance(card_ids, list):
            raise ValueError("column cardIds must be an array")
        for card_id in card_ids:
            if not isinstance(card_id, str) or not card_id.strip():
                raise ValueError("cardIds entries must be non-empty strings")
            if card_id not in cards:
                raise ValueError(f"card id '{card_id}' is missing from cards")
            if card_id in cards_seen_in_columns:
                raise ValueError(f"card id '{card_id}' appears in multiple columns")
            cards_seen_in_columns.add(card_id)

    for card_key, card in cards.items():
        if not isinstance(card_key, str) or not card_key.strip():
            raise ValueError("cards keys must be non-empty strings")
        if not isinstance(card, dict):
            raise ValueError("card entries must be objects")
        if card.get("id") != card_key:
            raise ValueError(f"card '{card_key}' id must match its key")
        if not isinstance(card.get("title"), str) or not card["title"].strip():
            raise ValueError(f"card '{card_key}' title must be a non-empty string")
        if not isinstance(card.get("details"), str):
            raise ValueError(f"card '{card_key}' details must be a string")
        if card_key not in cards_seen_in_columns:
            raise ValueError(f"card '{card_key}' is not assigned to any column")


def initialize_database(db_path: Path, seed_username: str = "user") -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_username = _normalize_username(seed_username)
    with _connect(db_path) as connection:
        connection.executescript(
            """
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
            """
        )
        user_id = get_or_create_user_id(connection, normalized_username)
        _create_default_board_if_missing(connection, user_id)


def get_or_create_user_id(connection: sqlite3.Connection, username: str) -> int:
    normalized_username = _normalize_username(username)
    existing = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (normalized_username,),
    ).fetchone()
    if existing:
        return int(existing["id"])

    cursor = connection.execute(
        "INSERT INTO users (username) VALUES (?)",
        (normalized_username,),
    )
    return int(cursor.lastrowid)


def _create_default_board_if_missing(connection: sqlite3.Connection, user_id: int) -> None:
    existing = connection.execute(
        "SELECT id FROM board_state WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if existing:
        return
    connection.execute(
        "INSERT INTO board_state (user_id, board_json, schema_version) VALUES (?, ?, 1)",
        (user_id, json.dumps(DEFAULT_BOARD)),
    )


def get_board_for_user(db_path: Path, username: str) -> dict[str, Any]:
    with _connect(db_path) as connection:
        user_id = get_or_create_user_id(connection, username)
        _create_default_board_if_missing(connection, user_id)
        row = connection.execute(
            "SELECT board_json FROM board_state WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("board row missing after initialization")
        board = json.loads(str(row["board_json"]))
        validate_board_data(board)
        return board


def update_board_for_user(db_path: Path, username: str, board: Any) -> dict[str, Any]:
    validate_board_data(board)
    with _connect(db_path) as connection:
        user_id = get_or_create_user_id(connection, username)
        _create_default_board_if_missing(connection, user_id)
        connection.execute(
            """
            UPDATE board_state
            SET board_json = ?, schema_version = 1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (json.dumps(board), user_id),
        )
        return board
