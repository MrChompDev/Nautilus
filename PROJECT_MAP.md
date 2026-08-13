# Nautilus OS — Project Map

A lightweight, low-RAM desktop environment for low-resource hardware (e.g. Raspberry Pi 500). Each application runs as an independent native process launched and orchestrated by the core shell.

---

## Tech Stack

| Layer | Technology | Version / Constraint |
| :--- | :--- | :--- |
| Language | Python | 3.11+ (target 3.13, 64-bit required) |
| GUI (shell + most apps) | PySide6 (Qt for Python) | `>=6.5.0` |
| Abyssal editor UI | PyQt5 | `>=5.15.0` |
| Riptide audio hub UI | PySide6 | `>=6.5.0` |
| Telemetry | psutil | `>=5.9.0` |
| Encryption (Surfline vault) | cryptography (AES-GCM) | `>=42.0` |
| Audio playback (Riptide) | pygame | `>=2.5.0` |
| HTTP clients | requests | `>=2.31.0` |
| Linting / formatting | ruff | `ruff.toml`, target `py313` |

Shared deps: `requirements.txt` (root). Per-app deps: `apps/<app>/requirements.txt`.

---

## Folder Structure

```text
nautilus/
├── core/                      # System shell, shared runtime, security
│   ├── main.py                # Desktop shell entry: floating glass bars, launchpad
│   ├── launcher.py            # APP_MANIFEST + AppLauncher (process lifecycle, IPC)
│   ├── theme.py               # Centralized design tokens + global QSS stylesheet
│   ├── logger.py              # Thread-safe structured logger (rotating file + ANSI console)
│   ├── auth.py                # Login dialog + JSON-backed account store (data/accounts.json)
│   ├── qt_env.py              # Qt plugin/DLL search-path bootstrap (call before QApplication)
│   ├── icons.py               # Programmatic SVG logo generation (cached to assets/logos/)
│   ├── wallpaper.py           # Programmatic desktop wallpaper renderer
│   └── security/              # Red/blue team tooling
│       ├── cli.py             # `py -3.13 -m core.security.cli ...` command surface
│       ├── scanner.py         # Network discovery (private ranges only, force-gated)
│       └── monitor.py         # Connections, processes, integrity baseline checks
├── apps/                      # Standalone applications (one folder each)
│   ├── Abyssal/               # Code editor / IDE (layered src/ package)
│   ├── Surfline/              # WebKit browser
│   ├── RipTide/               # Multi-provider audio + SFX hub (PySide6)
│   ├── Cinema/                # Media center (local-only, import your own media)
│   ├── Logbook/               # Markdown notes
│   ├── Mariner/               # Scientific calculator
│   ├── Current/               # System telemetry monitor
│   ├── Harbor/                # Keyboard-first file manager
│   ├── Tide/                  # Tabbed terminal (pure-Python internal shell)
│   ├── anchor/                # Control center / system settings
│   ├── Reef/                  # Local-first messenger (offline thread + IMAP/SMTP mail)
│   └── kraken/                # Local-first agentic AI engine + workforce (CLI + PySide6)
│       └── engine/
│           ├── spec.py        # Markdown Agent Builder (frontmatter + body → AgentSpec)
│           ├── agent_store.py # Custom agent catalog (~/.kraken/agents), name lookup
│           ├── providers.py   # OpenAI-compat + Anthropic wire formats, streaming client
│           ├── discovery.py   # Local model detection (Ollama/LM Studio/GGUF) + backend recommend
│           ├── keys.py        # API key store (keys.json → ~/.env → env vars)
│           ├── orchestrator.py# Workforce: planner/exec/qa roles, custom-agent role lookup
│           └── ...            # tools, memory, config, logger, agent
├── assets/                    # Generated logos (assets/logos/) + wallpaper.png
├── data/                      # Runtime state: accounts, security log, integrity baseline
├── logs/                      # Rotating nautilus.log output
├── docs/                      # Architecture docs & PRDs
├── agents/                    # Example Markdown agent specs (Kraken Agent Builder)
├── kraken.py                  # Kraken AI CLI entry point (cross-platform)
├── tests/
│   ├── smoke_test.py          # Offscreen launch/alive/kill test for every app
│   ├── test_kraken_engine.py  # Kraken engine unit tests (no backend required)
│   ├── test_kraken_agents.py  # Agent spec validation, catalog, role lookup, CLI dispatch
│   └── test_kraken_providers.py # Keys, model discovery, Anthropic/Gemini wire formats
├── requirements.txt           # Shared Python dependencies
├── pyproject.toml             # Kraken AI packaging: `kraken` + `kraken-gui` console scripts
├── ruff.toml                  # Lint configuration
└── PROJECT_MAP.md             # This file
```

---

## Key Entry Points

| Entry Point | Purpose |
| :--- | :--- |
| `core/main.py` | **Desktop shell.** Login → `NautilusShell` (floating glass top bar, wallpaper + clock card, centered glass dock, app grid launchpad, tray, global shortcuts). Ctrl+Space search overlay; Meta/Ctrl+Alt+G launchpad. |
| `core/launcher.py` | `APP_MANIFEST` routing table (app id → entry, shortcut, RAM target) + `AppLauncher` launch/terminate engine. |
| `core/search.py` | **Offline-first global search.** Pure-stdlib app/file index + web-engine URL builder (`~/.nautilus/search.json`). |
| `core/search_overlay.py` | Ctrl+Space overlay: apps / local files / web results (web opens in Surfline via URL argv). |
| `apps/<App>/main.py` | Each app's process entry. All follow the same bootstrap: inject `PROJECT_ROOT` into `sys.path`, call `core.qt_env.setup_qt_environment()`, then build a `QApplication` and apply `core.theme` palette + stylesheet. |
| `apps/Abyssal/application.py` | Example of the richer app layout: `AbyssalMainWindow` composes `src/views/*` (VS Code-style) around `src/ui/editor.py`. |
| `core/security/cli.py` | `python -m core.security.cli <cmd>` security toolkit CLI. |
| `kraken.py` | **Kraken AI CLI.** Interactive REPL, direct tasks, `--agent-mode` workforce, `build --spec`, `doctor`, `config`, `models`, `memory`. |
| `apps/kraken/main.py` | **Kraken AI desktop app.** PySide6 chat + real-time workforce tree; launched by the shell via `Ctrl+Alt+K`. |
| `tests/smoke_test.py` | Spawns every app with `QT_QPA_PLATFORM=offscreen`, verifies it survives N seconds, then kills it. |
| `tests/test_kraken_engine.py` | Kraken engine unit tests: spec parsing, memory loop, tools, safety gates (no backend required). |

---

## Core Design Patterns

- **Manifest-driven process orchestration.** `core/launcher.py` holds a single `APP_MANIFEST` dataclass registry; the shell launches each app as a `subprocess.Popen` child process (`start_new_session=True`), tracks PIDs, and supports SIGTERM-then-SIGKILL teardown. Global shortcuts (`Ctrl+Alt+<letter>`) resolve through the same manifest.
- **Centralized design token system.** `core/theme.py` exports `COLORS`, `FONTS`, `SPACING`, `create_nautilus_palette()`, and `get_global_stylesheet()`. All apps import these so the zero-radius, seafoam/abyss aesthetic stays consistent. App-local themes (e.g. `apps/Abyssal/src/ui/styles.py`) exist for app-specific overrides.
- **Shared runtime bootstrap.** Every app repeats the same prologue: add project root to `sys.path` → `setup_qt_environment()` → build `QApplication` → apply Nautilus palette/stylesheet. This lets apps run both standalone and from the shell.
- **Process-per-app isolation.** Each application is a separate OS process; the shell communicates via process handles and callbacks (`on_launch` / `on_exit`) rather than in-process imports. Abyssal additionally uses an in-app `EventBus` singleton (`apps/Abyssal/src/core/event_bus.py`) with `@on(event)` decorators for decoupled UI wiring.
- **Kraken engine (apps/kraken).** Model-agnostic OpenAI-compatible chat client (Ollama / LM Studio / vLLM / llama.cpp), Markdown-driven agent specs (`agents/*.md` frontmatter → system prompt + tool permissions), a SQLite error-learning memory (`~/.kraken/memory.db`), a self-correcting tool loop, and an orchestrator/worker workforce for `--agent-mode`. Local-first, zero-cost, and GUI-safe (engine events marshalled to the Qt thread via a polled queue).
- **Structured subsystem logging.** `core/logger.py` provides a singleton `NautilusLogger` with category-prefixed loggers (`CORE`, `LAUNCHER`, `THEME`, `IPC`, `APP`, `SYSTEM`, `PERF`), rotating file handler (5 MB × 7), and ANSI-colored console output.
- **Programmatic asset generation.** Logos (`core/icons.py`) and wallpaper (`core/wallpaper.py`) are rendered at runtime with `QPainter` and cached into `assets/`, avoiding binary asset bloat.
- **Data as plain files.** User/account data (`data/accounts.json`), security events (`data/security_log.jsonl`), and integrity baselines (`data/integrity_baseline.json`) are JSON/JSONL-backed for auditability.

---

## Development Commands

```sh
# Launch the desktop shell
py -3.13 core/main.py

# Run an app standalone
py -3.13 apps/Abyssal/main.py

# Run the Kraken AI desktop app
py -3.13 apps/kraken/main.py

# Kraken AI CLI
py -3.13 kraken.py --agent-mode "build a REST API for Logbook"
py -3.13 kraken.py build --spec agents/DatabaseArchitect.md

# Kraken engine unit tests
py -3.13 tests/test_kraken_engine.py

# Install the Kraken CLI anywhere (`kraken` on your PATH, no mandatory deps)
pip install .

# Install the standalone desktop app too (adds PySide6)
pip install ".[gui]"

# After installing: `kraken` (REPL), `kraken "task"`, `kraken --agent-mode "..."`
kraken doctor

# Smoke-test all apps (offscreen)
py -3.13 tests/smoke_test.py [--duration 4] [--app cinema]

# Lint
ruff check .

# Security toolkit CLI
py -3.13 -m core.security.cli --help
```
