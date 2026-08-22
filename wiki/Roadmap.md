# Roadmap

The project was [restarted from scratch](Project-History.md) — v1's full
application suite was removed and is being rebuilt from the core up. This page
is the master plan: milestones, every planned app with its feature set, and
release engineering. The actionable checklist version lives in
[`../TODO.md`](../TODO.md).

Status vocabulary used throughout: **Working** · **In progress** · **Reserved**
(button/dock slot exists) · **Planned** (designed, not started) · **Not
started**.

---

## Guiding principles

1. **Core first.** The shell must be a solid launcher before apps pile onto it.
2. **Small apps before big ones.** Utility apps (calculator, notes, terminal)
   land value fast and exercise the theme/bootstrap patterns cheaply.
3. **Every app runs standalone** (`python3 apps/<App>/main.py`) *and* from the
   dock — same bootstrap pattern everywhere.
4. **Tokens only.** No hardcoded colors/fonts/radii; everything reads
   `core/theme.py`.
5. **Pi 500 budget.** Keep the desktop shell lean (v1 target was under 350 MB
   RSS at idle); prefer stdlib over new dependencies.
6. **Old code is recoverable.** The v1 implementation of every app still exists
   in git history before commit `c9cf26a` — port and clean rather than rewrite
   from nothing where it makes sense.

## Dependency notes

- **App registry** (core) unblocks: dock buttons for all apps, app grid,
  keyboard shortcuts, global search targets.
- **Tide's internal shell** unblocks: Abyssal's integrated terminal.
- **Theme/settings storage** (Anchor) unblocks: user preferences across apps.
- **Kraken engine** unblocks: agent-driven features inside other apps later.

---

## M0 — Shell foundation

Goal: the shell behaves like a desktop, not a demo window. All work in `core/`.

| Item | Detail | Status |
| :--- | :--- | :--- |
| Dock anchoring | Remove hardcoded `(440, 650)`; recenter dock in `resizeEvent` | Not started |
| App registry | One table in `core/`: name → module/class/icon/shortcut; drives dock + future grid | Not started |
| Generic launching | `launch_app` instantiates any registered app; keeps references alive | Not started |
| Shortcuts | `Ctrl+Alt+<letter>` per app, `F11` fullscreen, `Meta` app-grid hook | Not started |
| Desktop surface | Generated wallpaper, clock/greeting card, right-click menu (launch, grid, shutdown) | Not started |
| Shell lifecycle | Graceful shutdown action, minimize-to-tray option | Not started |
| Logging | Shared logger writing under `logs/` | Not started |
| Knowledge map | `PROJECT_BRAIN.py` referenced by `AGENTS.md` — create and maintain | Not started |

Exit criteria: dock survives resizing, three placeholder buttons become
registry entries, hotkeys open registered apps, wallpaper renders.

## M1 — Surfline completion

Surfline is half-built; finish it before starting new apps so the browser
pattern (tabs, settings, persistence) is proven once.

| Item | Detail | Status |
| :--- | :--- | :--- |
| Real tabs | One `QWebEngineView` per tab, switchable strip, close buttons, `+` opens true blank/home tab | In progress |
| Nav sync | Back/forward/reload/home act on the active tab; omnibox mirrors it | In progress |
| Omnibox hardening | Scheme detection, localhost/IP handling, paste-and-go | Not started |
| Browsing extras | Zoom controls, find-in-page, history list | Not started |
| Persistence | Session restore (tabs/URLs) between runs | Not started |
| Password vault | AES-GCM vault via `cryptography` (already pinned in requirements) | Not started |

Exit criteria: multi-tab browsing is comfortable enough to be your default
browser on the Pi.

## M2 — Daily-driver apps (small, high value)

| App | Purpose | Key features | New deps | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Logbook** (`apps/Logbook/`) | Markdown notes | Editor + live preview pane, note list sidebar, full-text search, archive in `~/Documents/Logbook/` | none | Planned |
| **Mariner** (`apps/Mariner/`) | Scientific calculator | Expression eval with safe function whitelist, history tape, memory keys, nautical units (kn, nm, ftm, °C/°F) | none | Planned |
| **Tide** (`apps/Tide/`) | Terminal | Tabbed sessions, **pure-Python internal shell** (cd/pwd/env/ls/cat-style builtins — no external `$SHELL` needed), copy/paste, font-size controls | none | Planned |
| **Harbor** (`apps/Harbor/`) | File manager | Dual panes, keyboard-first navigation, copy/move/delete/rename, file-type previews, hidden-files toggle, bookmarks | none | Planned |

Order within M2: Logbook → Mariner → Tide → Harbor (each is independent;
this is easiest-to-hardest).

## M3 — System awareness

| App | Purpose | Key features | New deps | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Current** (`apps/Current/`) | Telemetry monitor | CPU/RAM/thermal live graphs, per-process table, kill button — vital on an 8 GB Pi | psutil | Planned |
| **Anchor** (`apps/anchor/`) | Settings hub | Display (resolution/orientation), network status, audio volume, theme/token viewer, about panel; persists user prefs for all apps | none | Planned |

Anchor also introduces the settings-storage convention (`~/.nautilus/*.json`)
other apps will reuse.

## M4 — Media

| App | Purpose | Key features | New deps | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Cinema** (`apps/Cinema/`) | Local media center | Import movie/show folders, poster-grid library, playback via QtMultimedia, resume positions | none | Planned |
| **Riptide** (`apps/RipTide/`) | Audio hub | Local library playback, SFX soundboard pads, optional streaming providers | requests, pygame | Planned |

## M5 — Power tools

| App | Purpose | Key features | New deps | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Abyssal** (`apps/Abyssal/`) | Code editor / IDE | Multi-file tree, syntax highlighting, command palette, integrated terminal (reuses Tide's internal shell), run-current-file | none (decision pending: custom highlighter vs QScintilla) | Reserved |
| **Kraken AI** (`apps/kraken/`) | Local-first agentic engine | Stdlib engine, OpenAI-compatible adapters (Ollama/LM Studio/vLLM/llama.cpp), `kraken` CLI + `kraken-gui`, key management (`~/.kraken/keys.json`), agent-spec loader (format preserved in `agents/DatabaseArchitect.md`), error-learning memory | none mandatory; GUI extra = PySide6 | Reserved |

Notes:

- `pyproject.toml` still packages `kraken-ai` (entry points
  `kraken` / `kraken-gui`) — restore `apps/kraken/` to match, or defer the
  packaging until the engine returns.
- Training corpora remain intact under `models/data/` (personas: kraken,
  leviathan, megalodon, charybdis).

## M6 — Communication & release

| Item | Purpose | Key features | New deps | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Reef** (`apps/Reef/`) | Messenger | Offline thread store (`~/.reef/`), contacts, optional IMAP/SMTP mail bridge | stdlib (imaplib/smtplib) | Planned |
| **Test suite** (`tests/`) | Regression safety | `smoke_test.py` (launch every app headless ~4 s), unit tests per core module | none | Not started |
| **CI** | Keep main green | ruff check + smoke test on push | — | Not started |
| **Packaging** | Ship it | Entry points for all apps, PyInstaller build recipe | pyinstaller (dev-only) | Not started |
| **Pi image** | First-boot SD setup | Setup script: apt deps, fonts, venv, autostart shell | — | Not started |
| **Docs** | Keep honest | Update README/wiki per milestone; repopulate `docs/` PRDs | — | Ongoing |

---

## Milestone summary

| Milestone | Contents | Depends on |
| :--- | :--- | :--- |
| M0 | Shell foundation | — |
| M1 | Surfline completion | M0 (registry) helps, not required |
| M2 | Logbook, Mariner, Tide, Harbor | M0 |
| M3 | Current, Anchor | M0, Anchor wants settings store |
| M4 | Cinema, Riptide | M3 (Anchor volume integration nice-to-have) |
| M5 | Abyssal, Kraken | M2 (Tide shell), M1 (patterns) |
| M6 | Reef, tests, CI, packaging, Pi image | Everything above |

See [`../TODO.md`](../TODO.md) for the flat, checkable task list derived from
this plan.
