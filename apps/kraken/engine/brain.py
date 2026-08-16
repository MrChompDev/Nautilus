"""
Kraken AI — Project Brain.

The coding model's long-term memory of a workspace. Scans a project once,
extracts per-file summaries (purpose, symbols, first lines), and persists them
in SQLite so the model can answer questions about the codebase without
re-reading the tree on every query. Incremental: only changed files are
re-indexed on later scans.
"""

import hashlib
import json
import os
import re
import sqlite3
import threading

SYMBOL_RE = re.compile(
    r"^\s*(?:async\s+|export\s+)?"
    r"(?:def|class|func|function|fn|sub|proc|static)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\b",
    re.MULTILINE,
)
SHELL_RE = re.compile(r"^\s*(?:[A-Za-z0-9_.-]+\s*=\s*[A-Za-z0-9_]+)\s*$", re.MULTILINE)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".vscode"}
SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".woff", ".woff2",
             ".ttf", ".otf", ".mp4", ".mp3", ".zip", ".tar", ".gz", ".db", ".bin", ".pyc"}
MAX_FILE_BYTES = 256 * 1024


def _db_path(workspace: str) -> str:
    base = os.path.join(os.path.expanduser("~"), ".nautilus", "brain")
    os.makedirs(base, exist_ok=True)
    digest = hashlib.sha1(os.path.abspath(workspace).encode()).hexdigest()[:12]
    return os.path.join(base, f"{digest}.db")


def _extract_header(text: str, lang: str) -> str:
    lines = text.splitlines()[:24]
    header = []
    in_docstring = False
    for ln in lines:
        stripped = ln.strip()
        if not header and not stripped:
            continue
        if not header and stripped.startswith("#!"):
            continue
        if stripped.startswith(('"""', "'''")) and not in_docstring:
            in_docstring = True
            inner = stripped[3:]
            if inner.endswith('"""') or inner.endswith("'''"):
                in_docstring = False
                inner = inner[:-3]
            inner = inner.strip().strip('"').strip("'")
            if inner:
                header.append(inner)
            continue
        if in_docstring:
            inner = stripped
            if stripped.endswith(('"""', "'''")):
                in_docstring = False
                inner = stripped[:-3]
            if inner.strip():
                header.append(inner.strip())
            continue
        if stripped.startswith(("#", "//", "*", ";")) or not stripped:
            header.append(stripped.lstrip("#/;* ").strip())
            if len(header) > 10:
                break
            continue
        break
    return " ".join(h for h in header if h)[:300]


class ProjectBrain:
    """Indexes a workspace once and serves project context for the coding model."""

    def __init__(self, workspace: str):
        self.workspace = os.path.abspath(workspace)
        self.db_path = _db_path(self.workspace)
        self._lock = threading.RLock()

    # ── storage ─────────────────────────────────────────────────
    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS files(
                relpath TEXT PRIMARY KEY,
                mtime REAL, size INTEGER, lang TEXT,
                header TEXT, symbols TEXT, preview TEXT)"""
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lang ON files(lang)")
        return conn

    # ── scanning ────────────────────────────────────────────────
    def scan(self, force: bool = False) -> dict:
        """Index the workspace. Returns a summary dict."""
        added = updated = unchanged = removed = skipped = 0
        with self._lock:
            conn = self._conn()
            known = dict(conn.execute("SELECT relpath, mtime FROM files").fetchall())
            seen = set()

            for dirpath, dirnames, filenames in os.walk(self.workspace):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    if fn.startswith("."):
                        continue
                    ext = os.path.splitext(fn)[1].lower()
                    if ext in SKIP_EXTS:
                        continue
                    full = os.path.join(dirpath, fn)
                    try:
                        st = os.stat(full)
                    except OSError:
                        skipped += 1
                        continue
                    if st.st_size > MAX_FILE_BYTES:
                        skipped += 1
                        continue
                    rel = os.path.relpath(full, self.workspace)
                    seen.add(rel)
                    if not force and known.get(rel) is not None and abs(known[rel] - st.st_mtime) < 1e-6:
                        unchanged += 1
                        continue
                    row = self._index_file(full, rel, st)
                    conn.execute(
                        "INSERT OR REPLACE INTO files(relpath,mtime,size,lang,header,symbols,preview) "
                        "VALUES(?,?,?,?,?,?,?)",
                        row,
                    )
                    if known.get(rel) is not None:
                        updated += 1
                    else:
                        added += 1

            for rel in set(known) - seen:
                conn.execute("DELETE FROM files WHERE relpath=?", (rel,))
                removed += 1
            conn.commit()
            total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            conn.close()
        return {"added": added, "updated": updated, "removed": removed,
                "unchanged": unchanged, "skipped": skipped, "total": total}

    def _index_file(self, full: str, rel: str, st: os.stat_result) -> tuple:
        try:
            with open(full, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            text = ""
        lang = os.path.splitext(rel)[1].lstrip(".").lower() or "txt"
        symbols = []
        for m in SYMBOL_RE.finditer(text):
            symbols.append(m.group(1))
        preview = "\n".join(text.splitlines()[:8])
        header = _extract_header(text, lang)
        return (rel, st.st_mtime, st.st_size, lang, header,
                json.dumps(symbols[:80]), preview)

    # ── queries ─────────────────────────────────────────────────
    def file_map(self) -> str:
        """Compact one-line-per-file tree for prompt injection."""
        conn = self._conn()
        rows = conn.execute("SELECT relpath, lang, header FROM files ORDER BY relpath").fetchall()
        conn.close()
        lines = []
        for rel, lang, header in rows:
            note = header[:60] if header else ""
            lines.append(f"- {rel} ({lang}){(' — ' + note) if note else ''}")
        return "\n".join(lines) or "(empty workspace)"

    def context(self, query: str, k: int = 6) -> str:
        """Top-k most relevant file summaries for a query."""
        tokens = set(re.findall(r"[A-Za-z0-9_]+", query.lower()))
        conn = self._conn()
        rows = conn.execute(
            "SELECT relpath, lang, header, symbols, preview, size FROM files"
        ).fetchall()
        conn.close()
        if not tokens:
            rows = rows[:k]
        scored = []
        for rel, lang, header, symbols, preview, size in rows:
            rel_l = rel.lower()
            header_l = header.lower()
            symbols_l = symbols.lower()
            preview_l = preview.lower()
            score = 0
            for t in tokens:
                if t in rel_l:
                    score += 3
                elif t in header_l or t in symbols_l:
                    score += 2
                elif t in preview_l:
                    score += 1
            scored.append((score, rel, lang, header, symbols, preview, size))
        scored.sort(key=lambda x: -x[0])
        out = []
        for score, rel, lang, header, symbols, preview, size in scored[:k]:
            syms = json.loads(symbols) if symbols else []
            out.append(f"[{rel} · {lang} · {size}B]")
            if header:
                out.append(f"  purpose: {header}")
            if syms:
                out.append(f"  symbols: {', '.join(syms[:20])}")
        return "\n".join(out) or "(no indexed files)"

    def status(self) -> dict:
        conn = self._conn()
        total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        by_lang = dict(conn.execute("SELECT lang, COUNT(*) FROM files GROUP BY lang").fetchall())
        conn.close()
        return {"workspace": self.workspace, "files": total, "languages": by_lang,
                "db": self.db_path}
