# Nautilus OS — Master TODO

The flat, checkable task list behind the [full roadmap](wiki/Roadmap.md).
Work top to bottom within each section; sections are ordered by priority.

Legend: `[ ]` open — `[x]` done.

## 0. Shell foundation (core/)

- [ ] Dock: remove hardcoded `(440, 650)`, recenter on `resizeEvent`
- [ ] Core: create app registry table (name, module, class, shortcut, icon)
- [ ] Core: generic `launch_app` driven by the registry; keep per-app references alive
- [ ] Shell: `Ctrl+Alt+<letter>` shortcuts for every registered app
- [ ] Shell: `F11` fullscreen toggle and graceful shutdown action
- [ ] Desktop: generated wallpaper + clock/greeting card replacing the plain label
- [ ] Desktop: right-click menu (launch apps, app grid placeholder, shutdown)
- [ ] Core: shared logger writing under `logs/`
- [ ] Create `PROJECT_BRAIN.py` knowledge map expected by `AGENTS.md`

## 1. Surfline completion (apps/surfline/)

- [ ] Real tab model: one `QWebEngineView` per tab with switchable strip
- [ ] Tab strip: close buttons, active-tab highlight, `+` opens a real new tab
- [ ] Nav bar acts on the active tab only; omnibox mirrors active tab
- [ ] Omnibox hardening: scheme detection, localhost/IP handling
- [ ] Zoom controls and find-in-page
- [ ] Session restore: save/restore open tabs between runs
- [ ] Password vault (AES-GCM via `cryptography`)
- [ ] Add standalone entry point (`python3 -m apps.surfline` or `main.py` guard)

## 2. Daily-driver apps

### Logbook (`apps/Logbook/`) — markdown notes
- [ ] Bootstrap skeleton following the shell pattern (path injection, theme import)
- [ ] Editor pane + live preview pane
- [ ] Note list sidebar with create/rename/delete
- [ ] Full-text search across notes
- [ ] Archive location `~/Documents/Logbook/`

### Mariner (`apps/Mariner/`) — calculator
- [ ] Expression evaluator with safe function whitelist
- [ ] History tape widget
- [ ] Memory keys (MS/MR/M+/M-)
- [ ] Nautical unit conversions (knots, nautical miles, fathoms, °C/°F)

### Tide (`apps/Tide/`) — terminal
- [ ] Tabbed terminal window skeleton
- [ ] Pure-Python internal shell: builtins (cd, pwd, env, ls, cat, echo), cwd tracking, env var handling
- [ ] Fallback execution of external commands via subprocess
- [ ] Copy/paste + font-size controls

### Harbor (`apps/Harbor/`) — file manager
- [ ] Dual-pane layout with focus switching
- [ ] Keyboard-first navigation (up/down/open/back)
- [ ] File operations: copy, move, delete, rename, new folder
- [ ] Previews for images/text/media types
- [ ] Hidden-files toggle + bookmarks

## 3. System apps

### Current (`apps/Current/`) — telemetry
- [ ] CPU / RAM / thermal live graphs (psutil)
- [ ] Per-process table sorted by usage
- [ ] Kill-process button with confirmation

### Anchor (`apps/anchor/`) — settings hub
- [ ] Settings storage convention: `~/.nautilus/*.json`
- [ ] Display panel (resolution/orientation)
- [ ] Network status panel
- [ ] Audio volume panel
- [ ] Theme/token viewer + accent picker
- [ ] About panel

## 4. Media apps

### Cinema (`apps/Cinema/`) — media center
- [ ] Import folders of movies/shows (scan + index)
- [ ] Poster-grid library view
- [ ] Playback via QtMultimedia
- [ ] Resume-position memory

### Riptide (`apps/RipTide/`) — audio hub
- [ ] Local library scan + playback list (pygame mixer)
- [ ] SFX soundboard pads with assignable samples
- [ ] Optional streaming providers (requests)

## 5. Power tools

### Abyssal (`apps/Abyssal/`) — IDE
- [ ] Decide highlighter approach (custom QSyntaxHighlighter vs QScintilla)
- [ ] Project tree + multi-file tabs
- [ ] Syntax highlighting for Python first
- [ ] Command palette
- [ ] Integrated terminal embedding Tide's internal shell
- [ ] Run-current-file button with output pane

### Kraken AI (`apps/kraken/`) — agentic engine
- [ ] Recover v1 engine code from git history (pre-`c9cf26a`) and clean it
- [ ] Engine core: pure stdlib, event queue, no Qt imports
- [ ] Provider adapters: Ollama, LM Studio, vLLM, llama.cpp, OpenAI-compatible
- [ ] Key management: `~/.kraken/keys.json` + env fallback
- [ ] Agent-spec loader (format preserved in `agents/DatabaseArchitect.md`)
- [ ] CLI: restore `kraken.py` shim surface (models/doctor/setup/chat/keys/agent)
- [ ] GUI chat window (`kraken-gui`, PySide6 optional extra)
- [ ] Verify `pyproject.toml` packaging matches restored package layout

## 6. Communication

### Reef (`apps/Reef/`) — messenger
- [ ] Offline thread store in `~/.reef/` (accounts.json, messages.json)
- [ ] Thread/compose UI
- [ ] Optional IMAP/SMTP mail bridge (stdlib imaplib/smtplib)

## 7. Release engineering

- [ ] Restore `tests/smoke_test.py` (headless launch of every app, ~4 s each)
- [ ] Unit tests for core modules (theme integrity, registry, logger)
- [ ] Headless env docs wired into test runner (`QT_QPA_PLATFORM=offscreen`, dummy SDL drivers)
- [ ] CI: ruff check + smoke test on push
- [ ] Packaging: entry points for all apps; PyInstaller recipe
- [ ] Raspberry Pi setup script: apt deps, fonts, venv, autostart
- [ ] Repopulate `docs/` with per-app PRDs as apps land
- [ ] Keep README + wiki in sync at each milestone

## Quick reference

```sh
python3 core/main.py          # run the OS
python3 -m ruff check .       # lint
```
