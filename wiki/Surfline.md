# Surfline Browser

**The Nautilus web browser** — a high-density WebKit/WebEngine browser with
dark mode, low-overhead tabs, and privacy features built in.

- **Launch:** `python3 apps/Surfline/main.py` or `Ctrl+Alt+S`
- **Memory target:** ~250 MB
- **UI:** PySide6 + QtWebEngine

## Overview

Surfline is the largest app in Nautilus. It accepts a URL as its first
argument (`python3 apps/Surfline/main.py https://example.com`) and opens it as
the initial tab — this is how the desktop's global search opens web results.

## Features

- **Tabbed browsing** — `QWebEngineView` tabs with a URL bar
  (`src/window.py:245`, ~1,760 lines).
- **ReefShield** — EasyList-style regex ad/tracker blocking via
  `ReefShieldFilter` and a request interceptor (`src/reef_shield/`).
- **TideSync** — JSON settings/history/bookmarks profiles, plus an optional
  AES-256-GCM password vault (PBKDF2-HMAC-SHA256, 200k iterations) via
  `cryptography` (`src/tide_sync/`).
- **Importer** — imports bookmarks, history, and passwords from
  Chrome/Firefox/Edge/Brave/Opera (via sqlite3) and CSV (`src/importer.py`).
- **Password manager** — view/save credentials for a site, backed by the
  vault (`src/dialogs.py`).
- **Persistent cache** — `assets/profiles/cache`, custom user agent
  `Surfline/1.0 (Developer Browser; ChompOS)`.
- **Dialogs & extras** — import dialog, settings dialog, JSON viewer
  (`JsonTreeWidget`), and an in-browser terminal widget.

## Dependencies

| Package | Purpose |
| :--- | :--- |
| PySide6 | Qt + QtWebEngine plugins (bundled, no extra pip) |
| `cryptography` | Password vault encryption (AES-GCM) |
| System libs | `libnss3`, `libxkbcommon0`, `libgl1`, `libegl1`, `libdbus-1-3` |

## Privacy

Surfline ships dark-mode-first and blocks trackers/ads by default through
ReefShield. Passwords are stored in an encrypted vault only if you enable it.
