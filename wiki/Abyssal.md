# Abyssal IDE

**A multi-language code editor with syntax highlighting and an integrated
terminal** — the Nautilus answer to a full IDE, tuned for low resource use.

- **Launch:** `python3 apps/Abyssal/main.py` or `Ctrl+Alt+A`
- **Memory target:** ~80 MB
- **UI:** PySide6

## Overview

Abyssal provides a familiar IDE layout: a menu bar, activity bar, sidebar, tab
bar with breadcrumbs, a split editor/terminal view, a status bar, and a
command palette. It is keyboard-first, with ~15 shortcuts wired up across the
editor.

## Features

- **AbyssalEditor** — `QPlainTextEdit` with a line-number gutter, active-line
  highlight, bracket matching, find/replace, and language auto-detection
  (`src/ui/editor.py`).
- **Syntax highlighting** — `QSyntaxHighlighter` engine covering ~35 file
  extensions: Python, JS/TS, C/C++, HTML/XML, CSS, Bash, JSON, YAML, Markdown
  (`src/engines/highlighter.py`).
- **Integrated terminal** — interactive `QProcess` shell with prompt and
  command history (`src/ui/terminal.py`).
- **Command palette** — quick access to commands via a popup.
- **Kraken chat dock** — right-side streaming AI chat (`Ctrl+Shift+C`, View
  menu). A background worker builds a `ChatClient` and streams responses in
  chunks; the workspace is set to the active file's folder so the coding model
  gets the project "brain" as context. History capped at 12 messages,
  `max_tokens` 256, model fallback coding → writing → pentest
  (`src/views/kraken_chat.py`).
- **File tree** — `QFileSystemModel`-based tree view (`src/ui/file_tree.py`).

## Shortcuts

| Keys | Action |
| :--- | :--- |
| `Ctrl+Shift+C` | Toggle Kraken AI chat panel |
| `Ctrl+P` | Command palette |
| `Ctrl+F` / `Ctrl+Shift+F` | Find / find in files |

## Architecture Notes

Two generations of the app coexist in the repo:

- **Live app** — direct Qt widget composition in `application.py`
  (`AbyssalMainWindow`, ~580 lines).
- **Documented service layer** — `src/core/` (EventBus, CommandRegistry, DI
  service container, keybindings), `src/models/` (TextDocument, EditorGroup),
  and rich views (file explorer, search panel, full Git client, 5-tab settings
  panel). Much of this is **not yet wired** into the running app; the live app
  currently uses only the highlighter, editor, and terminal from those layers.

### Known issues

- `_build_ui()` builds the editor/terminal splitter twice.
- Several services, models, LSP, and 8 of 15 views are not wired in.
- `config/workspace.json` is persisted but only loaded once.
- `requirements.txt` lists PyQt5 though the code imports PySide6.
