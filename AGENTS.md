# AGENTS.md

## Before any work — read the brain

Start every session by reading `PROJECT_BRAIN.py` (project knowledge map). It
contains the distilled architecture of the entire codebase — verified against
source. Do NOT crawl the repo for basic orientation; the brain has it.

```sh
python3 PROJECT_BRAIN.py        # quick overview
```

Useful queries (run via `python3 -c "import PROJECT_BRAIN as b; ..."`):
- `b.app("surfline")` — knowledge dict for one app
- `b.find("AbyssalMainWindow")` — locate any class/function by name
- `b.manifest()` — APP_MANIFEST routing table
- `b.commands()` — dev commands
- `b.design_patterns()` — conventions
- `b.dump()` — JSON snapshot for fast machine parsing

Keep `PROJECT_BRAIN.py` up to date when the structure changes.

## Project at a glance

- Nautilus OS: lightweight Python desktop environment (Raspberry Pi 500 target).
- Shell = `core/main.py`; 11 apps in `apps/` (one process each), registered in
  `APP_MANIFEST` (`core/launcher.py`).
- Every app bootstrap: inject project root into `sys.path` → `core.qt_env.setup_qt_environment()` → `QApplication` → Nautilus palette/stylesheet.
- Theme tokens live in `core/theme.py` (`COLORS`/`FONTS`/`SPACING`).
- Kraken AI (`apps/kraken`) is a local-first agentic engine, pure stdlib, with
  a CLI (`kraken.py`) and PySide6 GUI; engine never touches Qt (event queue).

## Commands

- Lint: `ruff check .`
- Tests: `python3 tests/smoke_test.py`, `python3 tests/test_kraken_*.py`
- Shell: `py -3.13 core/main.py` (or `python3`)
