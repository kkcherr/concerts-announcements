"""SQLite-backed store of canonical event keys already included in a digest."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


class StateStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self):
        con = sqlite3.connect(self.db_path)
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init_db(self) -> None:
        with self._conn() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_events (
                    canonical_key TEXT PRIMARY KEY,
                    first_seen_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )

    def filter_new(self, canonical_keys: list[str]) -> set[str]:
        """Return the subset of canonical_keys not already recorded as seen."""
        if not canonical_keys:
            return set()
        with self._conn() as con:
            placeholders = ",".join("?" for _ in canonical_keys)
            rows = con.execute(
                f"SELECT canonical_key FROM seen_events WHERE canonical_key IN ({placeholders})",
                canonical_keys,
            ).fetchall()
        already_seen = {row[0] for row in rows}
        return {key for key in canonical_keys if key not in already_seen}

    def mark_seen(self, canonical_keys: list[str]) -> None:
        if not canonical_keys:
            return
        with self._conn() as con:
            con.executemany(
                "INSERT OR IGNORE INTO seen_events (canonical_key) VALUES (?)",
                [(key,) for key in canonical_keys],
            )
