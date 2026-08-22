# Nautilus OS

**A lightweight desktop environment built entirely in Python on PySide6**
(Qt for Python) — designed with the Raspberry Pi 500 in mind and themed like a
ship at sea. A glass-surfaced shell, a token-driven design system, and a suite
of nautically named applications.

> **Status — v2 rebuild in progress.** Nautilus was previously a much larger
> system; it has been [restarted from scratch](wiki/Project-History.md) and is
> being rebuilt from the core up. Today you get the **desktop shell**, the
> **shared design system**, and the first app — the **Surfline web browser**.
> The rest of the app suite is on the [roadmap](#roadmap).

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Running](#running)
5. [Surfline Browser](#surfline-browser)
6. [Design System](#design-system)
7. [Roadmap](#roadmap)
8. [Repository Structure](#repository-structure)
9. [Development](#development)
10. [Documentation](#documentation)

---

## Features

What works today:

- **Desktop shell** (`core/main.py`) — a floating-glass top bar with live
  clock, a placeholder desktop surface, and a bottom dock for launching apps.
- **Design system** (`core/theme.py`) — one shared token set (colors, fonts,
  radii) driving every stylesheet; restyle the whole OS by editing one file.
- **Surfline browser** (`apps/surfline/app.py`) — Qt WebEngine browser with an
  omnibox (URLs *and* search), back/forward/reload/home, a themed start page,
  and a tab strip.

What makes it different:

- **Pure Python + Qt.** No C toolchain, no system services — just `python3`.
- **Token-driven theming.** Widgets never hardcode colors; everything reads
  from `core.theme`.
- **Warm "sand & coral" visual language** — translucent sand surfaces,
  wood tones, coral accents.
- **Nautical naming throughout** — every component is named like part of a
  ship (see the [wiki glossary](wiki/Glossary.md)).

## Requirements

| Requirement | Minimum |
| :--- | :--- |
| Python | **3.11+ 64-bit** (PySide6 requires 64-bit; project targets 3.13) |
| OS | Linux / Raspberry Pi OS / Windows |
| Display | 1080p capable; OpenGL/GLES needed by Qt WebEngine |
| RAM | 2 GB works, 8 GB recommended |

Python dependencies (`requirements.txt`):

| Package | Used by |
| :--- | :--- |
| `PySide6>=6.5.0` | UI framework — shell + every app |
| `psutil>=5.9.0` | Current telemetry app *(planned)* |
| `cryptography>=42.0` | Surfline password vault *(planned)* |
| `requests>=2.31.0` | Riptide audio APIs *(planned)* |
| `pygame>=2.5.0` | Riptide audio engine *(planned)* |

Everything else is pure stdlib.

## Installation

### 1. Clone

```sh
git clone https://github.com/anomalyco/Nautilus.git
cd Nautilus
```

### 2. Install Python dependencies

**Linux / Raspberry Pi OS** (venv recommended):

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

**Windows** (PySide6 needs 64-bit Python — target it explicitly):

```sh
py -3.13 -m pip install -r requirements.txt
```

### 3. System packages (Debian / Raspberry Pi OS only)

Qt WebEngine and the audio stack need a few native libraries:

```sh
sudo apt update
sudo apt install -y \
  libnss3 libasound2 libxkbcommon0 libxkbcommon-x11-0 \
  libgl1 libegl1 libdbus-1-3 fonts-noto-core
```

### 4. Recommended font

The theme uses JetBrains Mono for monospace text:

```sh
sudo apt install -y fonts-jetbrains-mono
```

## Running

From the repository root:

```sh
python3 core/main.py        # Linux / Raspberry Pi OS
py -3.13 core/main.py       # Windows
```

You'll see the Nautilus shell (1280×720):

- **Top bar** — translucent sand bar with the `NAUTILUS` wordmark and a live
  clock (updates every second).
- **Desktop** — warm sand backdrop with a centered title card.
- **Dock** — floating bar at the bottom with three launch buttons:
  **Surfline** (opens the browser), **Abyssal** and **Kraken**
  (placeholders — coming soon).

## Surfline Browser

Surfline is the first application of the v2 rebuild — your gateway to the web.

| Feature | Detail |
| :--- | :--- |
| Engine | Qt WebEngine (`QWebEngineView`, bundled with PySide6) |
| Omnibox | Type a domain → opens it over HTTPS; anything else → Google search |
| Navigation | Back `<` · Forward `>` · Reload `↻` · Home `⌂` |
| Start page | Themed HTML page with quick links (Google, YouTube, GitHub, Wikipedia) |
| Tabs | Tab strip present; real multi-tab switching is on the roadmap |

Launch it from the dock button, or run the shell and click **Surfline**.

## Design System

All visual language lives in [`core/theme.py`](core/theme.py). Apps import
tokens and build their stylesheets from them — no hardcoded colors anywhere.

| Token | Hex | Usage |
| :--- | :--- | :--- |
| Sand Light | `#E8DCC8` | Main window backdrops |
| Sand Mid | `#D4C8B0` | Toolbars, nav bars, dock buttons |
| Sand Dark | `#C2B49A` | Sidebars, tab strips |
| Wood | `#8B6F47` / `#A68B5B` / `#6B5535` | Wood-tone accents (light/base/dark) |
| Coral | `#FF6F61` | Primary accent — focus borders, links |
| Ink | `#1A1A1A` / `#2C2C2C` / `#4D4D4D` | Text (strong/body/muted) |
| Status | `#4CAF50` / `#FFC107` / `#F44336` | Success / warning / error |

Fonts: **Segoe UI** (UI), **JetBrains Mono** (technical text). Radius tokens:
`8px` / `12px` / `16px`. Shell surfaces render these at reduced alpha for the
glass effect.

Full reference: [wiki/Design-System.md](wiki/Design-System.md).

## Roadmap

The v1 suite is being rebuilt app by app:

| App | Purpose | Status |
| :--- | :--- | :--- |
| **Shell** | Desktop environment | Working |
| **Surfline** | Web browser | Working — tabs are a stub |
| **Abyssal** | Code editor & IDE | Dock button reserved |
| **Kraken AI** | Local-first agentic AI engine | Packaging + agent specs remain |
| **Riptide** | Audio hub + SFX soundboard | Planned |
| **Cinema** | Local media center | Planned |
| **Logbook** | Markdown notes with live preview | Planned |
| **Mariner** | Scientific calculator | Planned |
| **Current** | CPU/RAM/thermal monitor | Planned |
| **Harbor** | Dual-pane file manager | Planned |
| **Tide** | Tabbed terminal | Planned |
| **Anchor** | Settings & control center | Planned |
| **Reef** | Local messenger | Planned |

Near-term engineering TODOs:

- Center/anchor the dock on window resize (currently fixed at `(440, 650)`).
- Real tab management in Surfline (one `QWebEngineView` per tab).
- Standalone entry points per app (`python3 apps/<App>/main.py`).
- Restore the test suite under `tests/`.

The complete milestone-by-milestone plan is in
[wiki/Roadmap.md](wiki/Roadmap.md), with a flat checkable task list in
[`TODO.md`](TODO.md).

Dependencies for the planned apps are already pinned in `requirements.txt`.

## Repository Structure

```text
Nautilus/
├── AGENTS.md               # Instructions for AI coding agents
├── README.md               # This file
├── LICENSE                 # MIT
├── requirements.txt        # All OS + app Python dependencies
├── pyproject.toml          # Kraken AI packaging (`pip install .`)
├── ruff.toml               # Lint configuration
│
├── core/
│   ├── main.py             # Desktop shell entry point (TopBar, Dock, Shell)
│   └── theme.py            # Design tokens: COLORS, FONTS, RADIUS_*
│
├── apps/
│   └── surfline/
│       └── app.py          # Surfline browser (Qt WebEngine)
│
├── agents/
│   └── DatabaseArchitect.md  # Example Kraken agent spec
│
├── models/                 # AI training assets (~196 MB, standalone)
│   ├── data/               # Corpora per persona/domain
│   ├── lm/ · imggen/ · trained/
│   └── ...
│
├── wiki/                   # Project documentation (start at Home.md)
├── docs/                   # Architecture docs & PRDs (to be repopulated)
├── tests/                  # Test suite (to be restored)
├── data/ · logs/           # Runtime artifacts
└── .venv/                  # Local virtualenv (git-ignored)
```

## Development

Lint with [ruff](https://docs.astral.sh/ruff/) (config in `ruff.toml`,
line length 120, target `py313`):

```sh
python3 -m ruff check .
```

Headless/CI runs need dummy drivers for Qt:

```sh
export QT_QPA_PLATFORM=offscreen
export QTWEBENGINE_DISABLE_SANDBOX=1
```

Conventions:

- Import tokens from `core.theme`; never hardcode colors/fonts/radii.
- Every entry point injects the repo root into `sys.path` first, so modules
  run from any working directory.
- Scope QSS rules to widget classes; style normal/`:hover`/`:pressed` states.

## Documentation

Extended documentation lives in [`wiki/`](wiki/Home.md):

- [Architecture](wiki/Architecture.md) — how the system fits together
- [The Shell](wiki/Shell.md) — `core/main.py` deep dive
- [Surfline Browser](wiki/Surfline.md) — internals of the browser app
- [Design System](wiki/Design-System.md) — full token reference
- [Roadmap](wiki/Roadmap.md) — status of every component
- [Project History](wiki/Project-History.md) — v1 → v2 restart timeline
- [Glossary](wiki/Glossary.md) — the nautical naming scheme decoded

---

*MIT License — see [`LICENSE`](LICENSE).*
