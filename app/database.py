"""
Minimal SQLite-backed store for processed event IDs.

Why this file exists at all: real webhook providers frequently
re-send the same event (network retries, timeouts on their end where
they never got your 200 OK) - this is NORMAL provider behavior, not a
bug on either side. Without tracking which event_ids have already been
handled, a re-sent "payment succeeded" event gets processed twice -
which in a real system means a duplicate charge recorded, a duplicate
order shipped, or a duplicate CRM contact created. This file is what
prevents that.

WAL mode note: SQLite's default journal mode locks the whole database
file during a write, so if two webhooks arrive at almost the same
instant, the second one can hit "database is locked". WAL (Write-Ahead
Logging) mode lets reads and writes happen concurrently instead of
queueing behind a single lock - a real, worthwhile fix for a webhook
receiver that might get hit by bursts of events.
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "events.db"


def init_db(db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                received_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@contextmanager
def get_connection(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def is_duplicate(event_id: str, db_path: str = DB_PATH) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT 1 FROM processed_events WHERE event_id = ?", (event_id,)
        )
        return cursor.fetchone() is not None


def mark_processed(event_id: str, event_type: str, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO processed_events (event_id, event_type) VALUES (?, ?)",
            (event_id, event_type),
        )
