# Architecture

## Overview

Nautilus OS is a single-process desktop shell that spawns/hosts application
windows. It is built on **PySide6** and organized as:

```
core/main.py      ← shell entry point (QApplication + NautilusShell)
core/theme.py     ← shared design tokens (COLORS, FONTS, RADIUS_*)
apps/<app>/       ← one folder per app, self-contained Qt windows
```

## The bootstrap pattern

Every entry point follows the same three steps:

1. **Path injection** — `sys.path.insert(0, <project root>)` so modules can
   import `core.*` and `apps.*` regardless of the working directory
   (`core/main.py:6`).
2. **Theme import** — pull tokens from `core.theme`; never hardcode colors or
   fonts in widgets (see [Design System](Design-System.md)).
3. **Qt startup** — create a `QApplication`, build the top-level window,
   `show()`, then `app.exec()`.

## Process model

- The **shell** (`NautilusShell`) is the root window. It owns the TopBar, the
  content area, and the Dock.
- Apps are currently launched **in-process** — e.g. the dock instantiates
  `SurflineWindow` directly and keeps a reference on the shell
  (`self.browser = SurflineWindow()`, `core/main.py:147`). Keeping the reference
  is important: it prevents Python from garbage-collecting the window while it
  is open.
- The long-term plan (per README v1 design) is for each app to be its own
  **OS process** with a standalone entry point; the current restart starts with
  in-process hosting and can split later.

## Module map (current code)

| Module | Role |
| :--- | :--- |
| `core/main.py` | Shell: `TopBar`, `Dock`, `NautilusShell`, `main()` |
| `core/theme.py` | Design system: `COLORS`, `FONTS`, `RADIUS_SM/MD/LG` |
| `apps/surfline/app.py` | Surfline browser window (`SurflineWindow`) |
| `agents/*.md` | Kraken agent spec files (Markdown front-matter format) |

## Design principles

- **Token-driven styling** — all QSS is generated from f-strings over
  `core/theme.py` values, so restyling the OS means editing one file.
- **Nautical naming** — apps are ocean-themed; see [Glossary](Glossary.md).
- **Lightweight target** — designed to stay responsive on Raspberry Pi 500
  class hardware (see [Roadmap](Roadmap.md) for planned telemetry work).
