# Cinema

**A local-only, offline media center** — import your own movies and shows and
play them back full-screen. No servers, no streaming, no Jellyfin.

- **Launch:** `python3 apps/Cinema/main.py` or `Ctrl+Alt+M`
- **Memory target:** ~180 MB
- **UI:** PySide6 + QtMultimedia

## Overview

Cinema is the fully offline half of Nautilus. A sidebar offers Home, Movies,
Shows, Favorites, My Media, and Settings. Media is imported from your folders,
classified into Movies or TV, and played back locally.

## Features

- **Library scanning** — `LibraryScanner` walks media folders, builds a
  persistent JSON cache, and skips unchanged files via `.fingerprint` stale
  checks (`library.py`).
- **Smart import** — import files or whole folders (`_import_media` /
  `_import_folder`). Episodes matching the `[sS]\d{1,2}[eE]\d{1,2}` pattern go
  to `~/Cinema/TV/<show>`, everything else to `~/Cinema/Movies/<clean title>`
  (move or copy, your choice).
- **Full-screen playback** — `QMediaPlayer` + `QVideoWidget` in a dedicated
  `PlayerWindow` (`player.py`).
- **Favorites** — mark media as favorite and browse them in one place.
- **Media grid & cards** — responsive grid with cover-art caching and
  background art loaders; right-click context menu (Play / Favorite /
  Remove from Library) (`widgets.py`).
- **Background work** — scans and imports run in a `QThread` so the UI never
  freezes.

## Shortcuts

| Keys | Action |
| :--- | :--- |
| `Ctrl+I` | Import media |
| `F5` | Rescan library |
| `Ctrl+F` | Search library |

## Note

Cinema is a piracy-aware app: a first-run disclaimer dialog appears, and
reminders show on the Home, My Media, and Settings panels.
