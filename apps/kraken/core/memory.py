"""Kraken AI — lightweight memory store.

SQLite-backed conversation memory so each creature remembers context.
"""

from __future__ import annotations

import os
import sqlite3
import time


class MemoryStore:
    def __init__(self, path: str, enabled: bool = True):
        self.enabled = enabled
        self._path = path
        self._conn: sqlite3.Connection | None = None
        if enabled:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            self._conn = sqlite3.connect(path)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS entries ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "role TEXT, content TEXT, creature TEXT, ts REAL"
                ")"
            )

    def remember(self, role: str, content: str, creature: str = "") -> int:
        if not self.enabled or not self._conn:
            return 0
        cur = self._conn.execute(
            "INSERT INTO entries (role, content, creature, ts) VALUES (?, ?, ?, ?)",
            (role, content, creature, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def recall(self, creature: str = "", limit: int = 10) -> list[dict]:
        if not self.enabled or not self._conn:
            return []
        if creature:
            rows = self._conn.execute(
                "SELECT role, content, creature, ts FROM entries WHERE creature=? "
                "ORDER BY id DESC LIMIT ?",
                (creature, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT role, content, creature, ts FROM entries "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [{"role": r, "content": c, "creature": cr, "ts": t} for r, c, cr, t in reversed(rows)]

    def stats(self) -> dict:
        if not self.enabled or not self._conn:
            return {"entries": 0}
        row = self._conn.execute("SELECT COUNT(*) FROM entries").fetchone()
        return {"entries": row[0] if row else 0}

    def clear(self, creature: str = ""):
        if not self.enabled or not self._conn:
            return
        if creature:
            self._conn.execute("DELETE FROM entries WHERE creature=?", (creature,))
        else:
            self._conn.execute("DELETE FROM entries")
        self._conn.commit()
