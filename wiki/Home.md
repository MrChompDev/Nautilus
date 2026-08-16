# Nautilus OS Wiki

Welcome to the **Nautilus OS** wiki — a lightweight, low-RAM desktop environment
for the Raspberry Pi 500, built entirely in Python on PySide6 (Qt for Python).

Nautilus is a floating-glass desktop shell with twelve native apps, each running
as its own isolated process. The whole system targets **under 350 MB of RAM at
the desktop shell** and stays usable on a 2 GB machine.

## Quick Facts

| | |
| :--- | :--- |
| **Primary target** | Raspberry Pi 500 (ARM64, 8 GB RAM recommended) |
| **Also runs on** | Any Linux / Windows machine with 64-bit Python 3.11+ |
| **UI framework** | PySide6 (Qt for Python) |
| **Shell memory base** | under 350 MB |
| **Design** | Translucent "glass" surfaces over a generated ocean wallpaper, seafoam `#00F2C2` accent on abyss-navy `#081626` |
| **License** | MIT |

## Getting Started

```sh
python3 core/main.py            # Linux / Raspberry Pi OS
py -3.13 core/main.py           # Windows
```

You boot into a **login dialog**, then the Nautilus desktop:

- **Top bar** — floating glass pill with logo, running-app indicators, CPU/RAM
  metrics, user avatar, clock, fullscreen and shutdown controls.
- **Desktop** — generated ocean wallpaper, a glass clock/greeting card, and a
  right-click menu.
- **Dock** — centered floating glass dock; the **⊞** button opens the full app
  grid, and each app tile shows a seafoam dot while running.
- **Launchpad** — full-screen app grid with a filter box and every app.

## Global Shortcuts

| Keys | Action |
| :--- | :--- |
| `Meta` / `Ctrl+Alt+G` | Toggle the app grid (Launchpad) |
| `Ctrl+Space` | Global search: apps + local files + web |
| `F11` / `Ctrl+Alt+F` | Toggle fullscreen / windowed |
| `Ctrl+Alt+Q` | Shut down Nautilus |
| `Ctrl+Alt+Esc` | Minimize the shell to the system tray |

## The Apps

Each app is an independent process with its own entry point and its own wiki
page:

| App | Shortcut | Memory | Page |
| :--- | :--- | :--- | :--- |
| **Abyssal IDE** | `Ctrl+Alt+A` | 80 MB | [Abyssal](https://github.com/MrChompDev/Nautilus/wiki/Abyssal) |
| **Surfline Browser** | `Ctrl+Alt+S` | 250 MB | [Surfline](https://github.com/MrChompDev/Nautilus/wiki/Surfline) |
| **Riptide Audio** | `Ctrl+Alt+R` | 60 MB | [Riptide](https://github.com/MrChompDev/Nautilus/wiki/Riptide) |
| **Cinema** | `Ctrl+Alt+M` | 180 MB | [Cinema](https://github.com/MrChompDev/Nautilus/wiki/Cinema) |
| **Logbook** | `Ctrl+Alt+L` | 40 MB | [Logbook](https://github.com/MrChompDev/Nautilus/wiki/Logbook) |
| **Mariner** | `Ctrl+Alt+E` | 20 MB | [Mariner](https://github.com/MrChompDev/Nautilus/wiki/Mariner) |
| **Current Telemetry** | `Ctrl+Alt+C` | 15 MB | [Current](https://github.com/MrChompDev/Nautilus/wiki/Current) |
| **Harbor File Manager** | `Ctrl+Alt+H` | 30 MB | [Harbor](https://github.com/MrChompDev/Nautilus/wiki/Harbor) |
| **Tide Terminal** | `Ctrl+Alt+T` | 25 MB | [Tide](https://github.com/MrChompDev/Nautilus/wiki/Tide) |
| **Anchor Settings** | `Ctrl+Alt+,` | 20 MB | [Anchor](https://github.com/MrChompDev/Nautilus/wiki/Anchor) |
| **Kraken AI** | `Ctrl+Alt+K` | 120 MB | [Kraken](https://github.com/MrChompDev/Nautilus/wiki/Kraken) |
| **Reef Messenger** | `Ctrl+Alt+Z` | 40 MB | [Reef](https://github.com/MrChompDev/Nautilus/wiki/Reef) |

## Shell & System

Beyond the apps, Nautilus ships a set of core system services:

- **NautilusShell** (`core/main.py`) — floating-glass desktop: top bar, dock,
  launchpad, tray, shortcuts, login gate.
- **AppLauncher** (`core/launcher.py`) — `APP_MANIFEST` routing table + process
  lifecycle (launch / track / terminate via process groups).
- **Theme** (`core/theme.py`) — centralized design tokens + global QSS
  stylesheet shared by the shell and every app.
- **Auth** (`core/auth.py`) — login gate with PBKDF2 hashing, lockout, and
  hashed sessions over the live wallpaper.
- **Icons & Wallpapers** (`core/icons.py`, `core/wallpaper.py`,
  `core/wallpapers.py`) — programmatic logo and wallpaper generation, cached to
  `assets/`.
- **Global Search** (`core/search.py`, `core/search_overlay.py`) —
  offline-first search across apps, files, and web, bound to `Ctrl+Space`.
- **Kraken AI assets** (`core/ai_assets.py`) — optional local ComfyUI-based
  generator for wallpapers, app icons, and control icons (FLUX.2-klein).
- **Security toolkit** (`core/security/`) — opt-in red/blue team CLI for
  network discovery, monitoring, and integrity checks.

## Where Data Lives

| Location | Contents |
| :--- | :--- |
| `~/.kraken/` | Kraken config, API keys, agent specs, SQLite memory |
| `~/.reef/` | Reef messenger accounts + messages |
| `~/.nautilus/` | Wallpaper selection, search config, brain database |
| `~/Documents/Logbook/` | Logbook notes archive |
| `~/Cinema/Movies`, `~/Cinema/TV` | Imported Cinema media |
| `assets/logos/`, `assets/wallpapers/` | Generated logos and wallpapers |

## Design Tokens

| Token | Hex | Usage |
| :--- | :--- | :--- |
| Abyss Navy | `#081626` | Main window backdrops, root viewports |
| Slate Navy | `#0E2238` | Sidebars, toolbars, inactive panels |
| Seafoam | `#00F2C2` | Primary accent — carets, active borders, running dots |
| Coral | `#FF7F50` | Errors, warnings, shutdown |
| HD White | `#EEF4F8` | Primary text, mono fonts |

## Development

```sh
# Lint
python3 -m ruff check .

# Smoke-test every app (launches each standalone, 4 s each)
python3 tests/smoke_test.py
python3 tests/smoke_test.py --app tide

# Kraken engine unit tests
python3 tests/test_kraken_engine.py
python3 tests/test_kraken_agents.py
python3 tests/test_kraken_providers.py
```

See the [README](https://github.com/MrChompDev/Nautilus/blob/main/README.md)
for full installation instructions, the
[PROJECT_MAP](https://github.com/MrChompDev/Nautilus/blob/main/PROJECT_MAP.md)
for the repository layout, and
[PROJECT_BRAIN.py](https://github.com/MrChompDev/Nautilus/blob/main/PROJECT_BRAIN.py)
for the architecture knowledge map.
