"""Cinema — Nautilus Media Center.

Local media library scanner with a persistent JSON cache. Indexes movie and
TV show folders, extracting titles, years, and poster/backdrop art where
available, so the library UI never scans the disk on every launch.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v",
    ".wmv", ".flv", ".mpg", ".mpeg", ".ts", ".ogv",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}

# Common movie-title cleanup: "Movie.Name.2020.1080p.BluRay.x264-GROUP"
_TITLE_CLEANUP = re.compile(
    r"[.\-_ ]*(?:1080p|720p|2160p|480p|4k|bluray|web[-_ ]?dl|webrip|hdtv|dvdrip"
    r"|brrip|h265|x265|h264|x264|hevc|avc|aac|ac3|dd5\.1|dts|10bit|remux"
    r"|proper|repack|extended|theatrical|directors? cut|imax|bonus)"
    r"[.\-_ ]*",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"^(.*?)[.\-_ ]*\(?(\d{4})\)?.*$")


def _clean_title(name: str) -> str:
    base = os.path.splitext(name)[0]
    base = base.replace(".", " ")
    base = _TITLE_CLEANUP.sub(" ", base)
    base = re.sub(r"\s{2,}", " ", base).strip()
    m = _YEAR_RE.match(base)
    if m and m.group(2):
        year = m.group(2)
        title = m.group(1).strip()
        if title and len(title) >= 2:
            return f"{title} ({year})"
    return base or name


def _extract_year(name: str):
    base = os.path.splitext(name)[0]
    m = re.search(r"(?:^|[.\-_ ])(19\d{2}|20\d{2})(?:$|[.\-_ ])", base, re.IGNORECASE)
    return int(m.group(1)) if m else None


@dataclass
class MediaItem:
    id: str
    title: str
    year: int = 0
    path: str = ""
    kind: str = "movie"      # movie | episode
    overview: str = ""
    poster: str = ""         # local file path
    backdrop: str = ""
    server: str = ""         # legacy remote-server field (kept for cache compat)
    item_id: str = ""        # legacy remote item id (kept for cache compat)
    runtime_ms: int = 0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["poster"] = self._localize(d.get("poster") or "")
        return d

    @staticmethod
    def _localize(p: str) -> str:
        if p and os.path.sep in p:
            try:
                return str(Path(p))
            except Exception:
                return p
        return p

    @classmethod
    def from_dict(cls, d: dict) -> MediaItem:
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


class LibraryScanner:
    """Scan configured media folders and cache results to JSON."""

    def __init__(self, cache_dir: str):
        self._cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._cache_file = os.path.join(cache_dir, "library.json")
        self._lock = threading.Lock()

    # ── Cache ──

    def load_cache(self) -> list[MediaItem]:
        try:
            with open(self._cache_file, encoding="utf-8") as f:
                data = json.load(f)
            return [MediaItem.from_dict(d) for d in data]
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return []

    def save_cache(self, items: list[MediaItem]):
        with self._lock:
            tmp = self._cache_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump([i.to_dict() for i in items], f, indent=1, ensure_ascii=False)
            os.replace(tmp, self._cache_file)

    def cache_fingerprint(self, folders: list[str]) -> str:
        h = hashlib.sha256()
        for folder in sorted(folders):
            h.update(folder.encode("utf-8", "replace"))
            try:
                mtime = os.path.getmtime(folder)
                h.update(f"{mtime:.0f}".encode())
            except OSError:
                pass
        return h.hexdigest()

    # ── Scanning ──

    def scan(self, folders: list[str], progress=None) -> list[MediaItem]:
        """Scan folders. Returns media items.

        A folder is treated as a TV show if it contains multiple video files
        (episodes); otherwise each video file becomes a movie entry.
        """
        seen: dict[str, MediaItem] = {}
        for folder in folders:
            if not folder or not os.path.isdir(folder):
                continue
            for root, dirs, files in os.walk(folder):
                # Skip hidden and junk dirs
                dirs[:] = [d for d in dirs if not d.startswith(".")
                           and d.lower() not in ("subtitles", "subs", "extras",
                                                 "featurettes", "backdrops", "trailers")]
                videos = [f for f in files if os.path.splitext(f)[1].lower() in MEDIA_EXTENSIONS]
                if not videos:
                    continue

                images = [f for f in files if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
                poster = self._pick_poster(root, images)

                is_show = (self._looks_like_show_folder(root) or len(videos) > 1) and \
                    self._has_show_children(folder, root)

                if is_show:
                    for v in videos:
                        path = os.path.join(root, v)
                        title = _clean_title(v)
                        item = MediaItem(
                            id=self._item_id(path),
                            title=title,
                            year=_extract_year(v) or 0,
                            path=path,
                            kind="episode",
                            poster=poster,
                            overview=self._show_overview(root),
                            extra={"folder": root},
                        )
                        seen[item.id] = item
                else:
                    # Movie: the video file itself, or the containing folder
                    if len(videos) == 1 and self._is_self_contained_movie(root, files):
                        folder_name = os.path.basename(root)
                        item = MediaItem(
                            id=self._item_id(root),
                            title=_clean_title(folder_name),
                            year=_extract_year(folder_name) or 0,
                            path=os.path.join(root, videos[0]),
                            kind="movie",
                            poster=poster,
                            overview="",
                        )
                        seen[item.id] = item
                    else:
                        for v in videos:
                            path = os.path.join(root, v)
                            item = MediaItem(
                                id=self._item_id(path),
                                title=_clean_title(v),
                                year=_extract_year(v) or 0,
                                path=path,
                                kind="movie",
                                poster=poster,
                                overview="",
                            )
                            seen[item.id] = item
                if progress:
                    progress(len(seen))
        return list(seen.values())

    # ── Helpers ──

    @staticmethod
    def _looks_like_show_folder(path: str) -> bool:
        """True if the parent folder pattern looks like a show dir (Season x / show name)."""
        parent = os.path.basename(os.path.dirname(path))
        return bool(re.search(r"season\s*\d+", parent, re.IGNORECASE)) or \
            bool(re.search(r"\b(?:s\d{1,2}|s\d{1,2}e\d{1,2})\b", parent, re.IGNORECASE))

    @staticmethod
    def _has_show_children(scan_root: str, path: str) -> bool:
        rel = os.path.relpath(path, scan_root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        # Multi-file in a subfolder of a show root (e.g. Show/Season 1/) = episode
        return depth >= 1

    @staticmethod
    def _is_self_contained_movie(root: str, files: list[str]) -> bool:
        name = os.path.basename(root).lower()
        if len([f for f in files]) > 4:
            return False
        return not re.search(r"(s\d{1,2}(e\d{1,2})?|season)", name)

    @staticmethod
    def _pick_poster(root: str, images: list[str]) -> str:
        if not images:
            return ""
        lowered = {i.lower(): i for i in images}
        for key in ("poster", "folder", "cover", "fanart", "movie", "tv", "show"):
            if key in lowered:
                return os.path.join(root, lowered[key])
        return os.path.join(root, images[0])

    @staticmethod
    def _show_overview(root: str) -> str:
        for name in ("tvshow.nfo", "series.nfo", "movie.nfo"):
            p = os.path.join(root, name)
            if os.path.isfile(p):
                try:
                    with open(p, encoding="utf-8", errors="replace") as f:
                        text = f.read(2000)
                    import re as _re
                    m = _re.search(r"<plot>(.*?)</plot>", text, _re.IGNORECASE | _re.DOTALL)
                    return (m.group(1).strip() if m else text[:500]).strip()
                except Exception:
                    return ""
        return ""

    @staticmethod
    def _item_id(path: str) -> str:
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0
        return hashlib.sha256(f"{path}|{mtime}".encode()).hexdigest()[:16]
