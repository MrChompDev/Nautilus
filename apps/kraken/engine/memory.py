"""
Kraken AI — Local memory store.

A zero-dependency SQLite "vector memory" living at ~/.kraken/memory.db.

Agents persist failing stack traces / compiler output / user corrections
together with the fix that resolved them. Lookups run a lightweight
character-token cosine-style similarity over stored error signatures, so a
terminal error can be matched against past resolutions without any external
embedding service or network call (local-first by design).
"""

import json
import os
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9_]{3,}")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric token stream used for similarity scoring."""
    return _TOKEN_RE.findall(text.lower())


def _signature_embedding(text: str) -> list[float]:
    """Deterministic bag-of-tokens pseudo-embedding (TF-ish counts)."""
    counts: dict[str, float] = {}
    for tok in tokenize(text):
        counts[tok] = counts.get(tok, 0.0) + 1.0
    return [counts.get(t, 0.0) for t in sorted(counts)]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dots = sum(x * y for x, y in zip(a, b, strict=False))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if not na or not nb:
        return 0.0
    return dots / (na * nb)


def _vec_to_json(vec: list[float]) -> str:
    return json.dumps(vec)


@dataclass
class MemoryEntry:
    """One resolved error pattern from the learning loop."""

    error_signature: str
    fix_summary: str
    context: dict = field(default_factory=dict)
    source: str = "auto"
    created_at: float = field(default_factory=time.time)
    hits: int = 0
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


class MemoryStore:
    """Thread-safe SQLite store of resolved error patterns."""

    def __init__(self, path: str, enabled: bool = True):
        self.path = path
        self.enabled = enabled
        self._db: sqlite3.Connection | None = None
        if enabled:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            self._db = sqlite3.connect(path, check_same_thread=False)
            self._init_schema()

    def _init_schema(self):
        with self._db:
            self._db.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id TEXT PRIMARY KEY,
                    signature TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    fix TEXT NOT NULL,
                    context TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'auto',
                    created_at REAL NOT NULL,
                    hits INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self._db.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_signature ON memory(signature)"
            )

    # ── Writes ─────────────────────────────────────────────────
    def remember(
        self,
        error_signature: str,
        fix_summary: str,
        context: dict | None = None,
        source: str = "auto",
    ) -> str | None:
        """Persist an error → fix pair. Returns the entry id."""
        if not self.enabled or not self._db or not error_signature:
            return None
        entry = MemoryEntry(
            error_signature=error_signature,
            fix_summary=fix_summary,
            context=context or {},
            source=source,
        )
        try:
            with self._db:
                self._db.execute(
                    """
                    INSERT INTO memory (id, signature, embedding, fix, context, source, created_at, hits)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.entry_id,
                        entry.error_signature,
                        _vec_to_json(_signature_embedding(entry.error_signature)),
                        entry.fix_summary,
                        json.dumps(entry.context),
                        entry.source,
                        entry.created_at,
                        entry.hits,
                    ),
                )
            return entry.entry_id
        except sqlite3.Error:
            return None

    # ── Reads ──────────────────────────────────────────────────
    def recall(self, query: str, top_k: int = 3, min_score: float = 0.15) -> list[MemoryEntry]:
        """Return past resolutions ranked by signature similarity."""
        if not self.enabled or not self._db:
            return []
        query_vec = _signature_embedding(query)
        if not query_vec:
            return []
        try:
            with self._db:
                rows = self._db.execute(
                    "SELECT id, signature, fix, context, source, created_at, hits "
                    "FROM memory"
                ).fetchall()
        except sqlite3.Error:
            return []

        scored: list[tuple[float, MemoryEntry]] = []
        for row in rows:
            score = _cosine(query_vec, _signature_embedding(row[1]))
            if score >= min_score:
                entry = MemoryEntry(
                    entry_id=row[0],
                    error_signature=row[1],
                    fix_summary=row[2],
                    context=_safe_json(row[3]),
                    source=row[4],
                    created_at=row[5],
                    hits=row[6],
                )
                scored.append((score, entry))

        scored.sort(key=lambda pair: (-pair[0], -pair[1].hits))
        return [e for _, e in scored[:top_k]]

    def find_exact(self, signature: str) -> MemoryEntry | None:
        """Look up a previously seen error by its exact signature."""
        if not self.enabled or not self._db:
            return None
        try:
            with self._db:
                row = self._db.execute(
                    "SELECT id, signature, fix, context, source, created_at, hits "
                    "FROM memory WHERE signature = ? LIMIT 1",
                    (signature,),
                ).fetchone()
        except sqlite3.Error:
            return None
        if not row:
            return None
        return MemoryEntry(
            entry_id=row[0],
            error_signature=row[1],
            fix_summary=row[2],
            context=_safe_json(row[3]),
            source=row[4],
            created_at=row[5],
            hits=row[6],
        )

    def bump_hit(self, entry_id: str):
        if not self.enabled or not self._db:
            return
        try:
            with self._db:
                self._db.execute("UPDATE memory SET hits = hits + 1 WHERE id = ?", (entry_id,))
        except sqlite3.Error:
            pass

    def stats(self) -> dict[str, Any]:
        if not self.enabled or not self._db:
            return {"enabled": False, "entries": 0}
        try:
            with self._db:
                n = self._db.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
                top = self._db.execute(
                    "SELECT signature, hits FROM memory ORDER BY hits DESC LIMIT 5"
                ).fetchall()
            return {
                "enabled": True,
                "entries": n,
                "top_resolved": [{"signature": s, "hits": h} for s, h in top],
            }
        except sqlite3.Error:
            return {"enabled": True, "entries": 0, "top_resolved": []}

    def forget(self, entry_id: str) -> bool:
        if not self.enabled or not self._db:
            return False
        try:
            with self._db:
                cur = self._db.execute("DELETE FROM memory WHERE id = ?", (entry_id,))
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    def close(self):
        if self._db:
            try:
                self._db.close()
            except sqlite3.Error:
                pass
            self._db = None


def _safe_json(raw: str | bytes) -> dict:
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}
