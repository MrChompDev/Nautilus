"""Nautilus Search — offline-first global search. Pure stdlib, no Qt.

Local results (apps + files) never touch the network. Web results only build
a search URL from a user-chosen engine; fetching it is the browser's job.
"""

from __future__ import annotations

import json
import os
import re
from urllib.parse import quote_plus

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".nautilus")
CONFIG_PATH = os.path.join(CONFIG_DIR, "search.json")

SEARCH_ENGINES: dict[str, tuple[str, str]] = {
    "duckduckgo": ("DuckDuckGo", "https://duckduckgo.com/?q={}"),
    "google": ("Google", "https://www.google.com/search?q={}"),
    "bing": ("Bing", "https://www.bing.com/search?q={}"),
    "brave": ("Brave", "https://search.brave.com/search?q={}"),
    "startpage": ("Startpage", "https://www.startpage.com/do/search?q={}"),
    "mojeek": ("Mojeek", "https://www.mojeek.com/search?q={}"),
    "yahoo": ("Yahoo", "https://search.yahoo.com/search?p={}"),
}

DEFAULT_ROOTS = (
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Documents/Logbook"),
    os.path.expanduser("~/Notes"),
)


def _defaults() -> dict:
    return {"engine": "duckduckgo", "roots": []}


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        cfg = {}
    merged = _defaults()
    if isinstance(cfg, dict):
        merged.update(cfg)
    return merged


def save_config(cfg: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_engine() -> str:
    return load_config().get("engine", "duckduckgo")


def set_engine(name: str) -> None:
    if name not in SEARCH_ENGINES:
        raise ValueError(f"unknown engine: {name}")
    cfg = load_config()
    cfg["engine"] = name
    save_config(cfg)


def get_roots() -> list[str]:
    cfg = load_config()
    roots = list(cfg.get("roots") or [])
    roots = [os.path.expanduser(r) for r in roots]
    for d in DEFAULT_ROOTS:
        expanded = os.path.expanduser(d)
        if expanded not in roots and os.path.isdir(expanded):
            roots.append(expanded)
    return roots


def set_roots(roots: list[str]) -> None:
    cfg = load_config()
    cfg["roots"] = [os.path.abspath(r) for r in roots if os.path.isdir(r)]
    save_config(cfg)


def build_search_url(query: str, engine: str | None = None) -> str:
    name = engine or get_engine()
    template = SEARCH_ENGINES.get(name, SEARCH_ENGINES["duckduckgo"])[1]
    return template.replace("{}", quote_plus(query))


def match_apps(query: str, manifest: dict) -> list[dict]:
    """Fuzzy-match installed apps by id/name/description."""
    q = query.strip().lower()
    if not q:
        return []
    tokens = [t for t in re.split(r"\s+", q) if t]
    scored = []
    for app_id, entry in manifest.items():
        score = 0
        for tok in tokens:
            if tok in app_id.lower():
                score += 4
            if tok in entry.name.lower():
                score += 3
            if tok in entry.description.lower():
                score += 1
        if score:
            scored.append((score, app_id, entry))
    scored.sort(key=lambda x: -x[0])
    return [
        {"kind": "app", "app_id": app_id, "title": entry.name,
         "detail": entry.description}
        for _, app_id, entry in scored[:12]
    ]


def match_files(query: str, roots: list[str] | None = None,
                limit: int = 25) -> list[dict]:
    """Name-based local file search under the configured roots."""
    q = query.strip().lower()
    if not q:
        return []
    hits: list[tuple[int, str, int]] = []
    for root in (roots if roots is not None else get_roots()):
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                if q in name.lower():
                    full = os.path.join(dirpath, name)
                    try:
                        size = os.path.getsize(full)
                    except OSError:
                        size = 0
                    hits.append((name.lower().count(q), full, size))
    hits.sort(key=lambda x: (-x[0], x[1].lower()))
    return [
        {"kind": "file", "path": path, "title": os.path.basename(path),
         "detail": path, "size": size}
        for _, path, size in hits[:limit]
    ]


def search_all(query: str, manifest: dict,
               roots: list[str] | None = None) -> list[dict]:
    """Combined app + local-file results. Network-free."""
    return match_apps(query, manifest) + match_files(query, roots)


def web_result(query: str, engine: str | None = None) -> dict:
    return {
        "kind": "web",
        "engine": engine or get_engine(),
        "title": f"Search the web: {query}",
        "url": build_search_url(query, engine),
    }
