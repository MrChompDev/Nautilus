# Roadmap

The project was [restarted from scratch](Project-History.md) — v1's full
application suite was removed and is being rebuilt. This page tracks what
exists today vs. what is planned.

## Current status (v2)

| Component | State |
| :--- | :--- |
| Shell (`core/main.py`) | Working: TopBar with clock, placeholder desktop, dock |
| Design system (`core/theme.py`) | Working: sand/wood/coral token set |
| Surfline browser | Working: nav, omnibox, home page; tab switching is a stub |
| Dock buttons Abyssal / Kraken | Placeholders (print only) |

## Planned apps (from the v1 design, to be rebuilt)

| App | Purpose | Status |
| :--- | :--- | :--- |
| **Abyssal** | Code editor & IDE (multi-language, command palette, terminal) | Reserved — dock button exists |
| **Kraken AI** | Local-first agentic engine + chat GUI ([details](Kraken-AI.md)) | Packaging/specs remain; engine code removed |
| **Riptide** | Audio hub + SFX soundboard (requests + pygame) | Planned |
| **Cinema** | Local media center for your own movies/shows | Planned |
| **Logbook** | Markdown notes with live preview + search | Planned |
| **Mariner** | Scientific calculator, history tape, nautical units | Planned |
| **Current** | CPU/RAM/thermal telemetry + process kill (psutil) | Planned |
| **Harbor** | Dual-pane keyboard-first file manager | Planned |
| **Tide** | Tabbed terminal with a pure-Python internal shell | Planned |
| **Anchor** | Settings/control center (display, network, audio, theme) | Planned |
| **Reef** | Local-first messenger (offline thread + optional IMAP/SMTP) | Planned |

## Engineering TODOs visible in the code

- **Dock layout** — hardcoded position `(440, 650)` in `core/main.py:141`;
  should center/anchor on window resize.
- **Surfline tabs** — implement real tab switching (one `QWebEngineView` per
  tab) instead of reusing the single view (`apps/surfline/app.py:169`).
- **Standalone app entry points** — apps currently have no `__main__` guard;
  v1 ran each as `python3 apps/<App>/main.py`.
- **README alignment** — README still documents the v1 palette (`#081626`
  abyss navy / seafoam `#00F2C2`) while v2 uses the sand/coral theme; it also
  references modules (launcher, auth, search…) not yet rebuilt.
- **PROJECT_BRAIN.py** — referenced by `AGENTS.md` as the project knowledge map
  but not present yet.

Dependencies for planned apps are already pinned in `requirements.txt`
(`psutil`, `cryptography`, `requests`, `pygame`), so rebuilding them needs no
new packages.
