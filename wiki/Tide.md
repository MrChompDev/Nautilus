# Tide Terminal

**A GPU-accelerated, multi-tab terminal emulator with a pure-Python internal
shell** — no external `$SHELL` required.

- **Launch:** `python3 apps/Tide/main.py` or `Ctrl+Alt+T`
- **Memory target:** ~25 MB
- **UI:** PySide6

## Overview

Tide is Nautilus' terminal. Unlike typical terminal apps, its shell is
**`InternalShell`** (`apps/Tide/shell.py`) — a pure-Python shell with no
dependency on `/bin/bash` or any external process. That makes it fully
self-contained and predictable on the Pi.

## Features

- **InternalShell** — tokenizer handling quotes/escapes, `&&` `||` `;` `|`
  `<` `>` `>>` pipes and redirections, `$VAR` and `~` expansion, 30 built-ins,
  and direct external processes (`Popen`, `shell=False`, streaming). Supports
  `request_abort` for Ctrl+C.
- **Multi-tab** — closable, movable tabs; the tab title tracks the current
  directory.
- **Non-blocking** — each session runs a `CommandWorker` (`QThread`) around a
  shared `InternalShell`, so long commands never freeze the UI.
- **Styled output** — distinct styling for stdout, stderr, system messages,
  dim text, and accents.
- **History** — Up/Down recall per session via the shell.

## Shortcuts

| Keys | Action |
| :--- | :--- |
| `Ctrl+T` | New tab |
| `Ctrl+W` | Close tab |
| `Ctrl+C` | Interrupt (via `request_abort`) |
| `Ctrl+L` | Clear |
| `Ctrl+Tab` | Cycle tabs |
| `Up` / `Down` | Command history |

## Notes

Because Tide spawns its own processes directly rather than through a parent
shell, the launcher's process-group isolation is critical — Tide sessions are
tracked and torn down as part of the app's process group.
