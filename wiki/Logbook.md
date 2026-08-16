# Logbook

**Markdown notes with live preview, instant search, and auto-save** — Nautilus'
take on a notes app, kept deliberately simple.

- **Launch:** `python3 apps/Logbook/main.py` or `Ctrl+Alt+L`
- **Memory target:** ~40 MB
- **UI:** PySide6 (single file, ~530 lines)

## Overview

Logbook is a three-pane splitter: a notes list on the left, a markdown editor
in the middle, and a live HTML preview on the right. Notes are stored as
plain `.md` files in `~/Documents/Logbook/` — no database, no lock-in.

## Features

- **Three-pane layout** — notes list | markdown editor | live preview.
- **Custom-safe renderer** — `_render_markdown()` renders headings, lists,
  code blocks, and rules without any markdown library (`markdown` is not a
  dependency).
- **Instant search** — matches note title and content as you type.
- **Auto-save** — every 2 seconds via a `QTimer` with dirty tracking, so you
  never lose a note.
- **Note management** — create, rename, and delete notes from the list.

## Shortcuts

| Keys | Action |
| :--- | :--- |
| `Ctrl+N` | New note |
| `Ctrl+F` | Find in note |
| `Ctrl+S` | Save |
| `Ctrl+Shift+P` | (palette) |
| `F2` / `R` | Rename note |
| `Delete` | Delete note |

## Data

Notes live as markdown files under `~/Documents/Logbook/` — edit them with any
editor outside Logbook if you like.
