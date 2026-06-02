"""
SQLite-backed deduplication store.
Tracks seen event IDs and announcement URLs so we never alert twice.
"""

import sqlite3
from contextlib import contextmanager
from config import DB_PATH


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with _conn() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source      TEXT NOT NULL,
                external_id TEXT NOT NULL,
                url         TEXT,
                seen_at     TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source, external_id)
            )
            """
        )


def is_seen(source: str, external_id: str) -> bool:
    with _conn() as con:
        row = con.execute(
            "SELECT 1 FROM seen_events WHERE source=? AND external_id=?",
            (source, str(external_id)),
        ).fetchone()
    return row is not None


def mark_seen(source: str, external_id: str, url: str = "") -> None:
    with _conn() as con:
        con.execute(
            "INSERT OR IGNORE INTO seen_events (source, external_id, url) VALUES (?,?,?)",
            (source, str(external_id), url),
        )


def filter_new(source: str, events: list[dict]) -> list[dict]:
    """
    Given a list of event dicts (each must have an 'id' key),
    return only those not yet seen and immediately mark them as seen.
    """
    new_events = []
    for event in events:
        eid = str(event.get("id", ""))
        url = event.get("url", "")
        if eid and not is_seen(source, eid):
            mark_seen(source, eid, url)
            new_events.append(event)
    return new_events
