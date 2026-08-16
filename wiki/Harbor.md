# Harbor File Manager

**A keyboard-first, dual-pane file manager with inline previews.**

- **Launch:** `python3 apps/Harbor/main.py` or `Ctrl+Alt+H`
- **Memory target:** ~30 MB
- **UI:** PySide6 (single file, ~720 lines)

## Overview

Harbor is built for speed with the keyboard. Two synchronized `FilePane`s sit
side by side; a `FilePreview` pane shows text/code inline (up to 1 MB) or
binary metadata for larger files.

## Features

- **Dual-pane navigation** — two independent panes with path bars,
  lazy-loaded directory trees, back/forward/up navigation, type-colored
  entries, and context menus.
- **Vim-style keys** — navigate without leaving the keyboard.
- **Preview pane** — inline text/code preview for files ≤ 1 MB, binary
  metadata otherwise.
- **Archive support** — create `.zip` / `.tar.gz` archives using stdlib
  `zipfile` + `tarfile`.

## Keyboard Map

| Keys | Action |
| :--- | :--- |
| `j` / `k` | Move down / up |
| `h` / `l` | Switch pane |
| `Enter` | Open selected |
| `Backspace` | Up one level |
| `Space` | Preview |
| `/` | Focus the path bar |
| `F5` | Copy |
| `F6` | Move |
| `F7` | Make directory |
| `F8` | Delete |
