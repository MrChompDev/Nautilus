# Nautilus OS

**A lightweight, low-RAM desktop environment for the Raspberry Pi 500** — built
entirely in Python on PySide6 (Qt for Python). A floating-glass desktop shell,
an ocean-themed token system, and twelve native apps that each run as their own
process.

- **Primary target:** Raspberry Pi 500 (ARM64, 8 GB RAM recommended)
- **Also runs on:** any Linux / Windows machine with 64-bit Python 3.11+
- **Memory base:** under 350 MB at the desktop shell
- **Design:** translucent "glass" shell surfaces over a generated ocean wallpaper,
  seafoam `#00F2C2` accent on abyss-navy `#081626`

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Running the Operating System](#running-the-operating-system)
4. [Keyboard Shortcuts](#keyboard-shortcuts)
5. [Applications](#applications)
6. [Kraken AI — CLI & GUI](#kraken-ai--cli--gui)
7. [Where Your Data Lives](#where-your-data-lives)
8. [Testing & Development](#testing--development)
9. [Repository Structure](#repository-structure)
10. [Design Tokens](#design-tokens)

---

## Requirements

| Requirement | Minimum |
| :--- | :--- |
| Python | **3.11+ 64-bit** (PySide6 requires 64-bit) |
| Disk | 1 GB free (repo + packages), 16 GB SD card recommended |
| Display | 1080p capable, OpenGL/GLES for WebEngine apps |
| RAM | 2 GB (8 GB recommended) |

Python packages are installed from `requirements.txt` — see below.

---

## Installation

### 1. Clone the repository

```sh
git clone https://github.com/anomalyco/Nautilus.git
cd Nautilus
```

### 2. Install Python dependencies

On **Linux / Raspberry Pi OS** (recommended: create a venv first):

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On **Windows** (PySide6 requires 64-bit Python — target it explicitly):

```sh
py -3.13 -m pip install -r requirements.txt
```

`requirements.txt` installs everything the OS and all apps need:

| Package | Used by |
| :--- | :--- |
| `PySide6>=6.5.0` | The Qt UI framework — shell + every app |
| `psutil>=5.9.0` | Current telemetry, shell CPU/RAM metrics |
| `cryptography>=42.0` | Surfline password-vault encryption (AES-GCM) |
| `requests>=2.31.0` | Riptide streaming APIs (Spotify / SoundCloud / YouTube) |
| `pygame>=2.5.0` | Riptide audio engine + SFX soundboard |

Everything else in the codebase is **pure Python stdlib** — including the Kraken
AI engine and the Reef messenger backend.

### 3. System packages (Debian / Raspberry Pi OS only)

PySide6 bundles Qt, but the web engine and audio stack need a few system libs:

```sh
sudo apt update
sudo apt install -y \
  libnss3 libasound2 libxkbcommon0 libxkbcommon-x11-0 \
  libgl1 libegl1 libdbus-1-3 \
  fonts-noto-core
```

Surfline and Cinema additionally use the Qt WebEngine / QtMultimedia plugins
that ship inside PySide6 — no extra pip packages required.

### 4. Optional: install the Kraken CLI

The Kraken AI engine is a separate, installable package (pure stdlib engine,
works headless):

```sh
pip install .            # installs the `kraken` CLI
pip install ".[gui]"     # + the `kraken-gui` desktop app (PySide6)
```

You can also run it without installing — see [Kraken AI](#kraken-ai--cli--gui).

### 5. Optional: recommended fonts

The UI looks best with the mono fonts used by the theme:

```sh
# Debian / Raspberry Pi OS
sudo apt install -y fonts-jetbrains-mono
```

---

## Running the Operating System

From the repository root (venv active):

```sh
python3 core/main.py            # Linux / Raspberry Pi OS
py -3.13 core/main.py           # Windows
```

You'll get a **login dialog**, then the Nautilus desktop:

- **Top bar** — floating glass pill with the logo, running-app indicators,
  CPU/RAM metrics, user avatar, clock, fullscreen and shutdown controls.
- **Desktop** — generated ocean wallpaper, a glass clock/greeting card, and a
  right-click menu (launch apps, open app grid, shutdown).
- **Dock** — centered floating glass dock. The **⊞** button opens the full app
  grid; each app tile shows a seafoam dot while the app is running.
- **App grid (Launchpad)** — full-screen overlay with a filter box and every app.

> `core/main.py` generates app logos into `assets/logos/` on first boot.

---

## Keyboard Shortcuts

| Keys | Action |
| :--- | :--- |
| `Meta` (Super/Win) **or** `Ctrl+Alt+G` | Toggle the app grid (Launchpad) |
| `Ctrl+Space` **or** `Ctrl+Alt+Space` | Global search: apps + local files + web |
| `F11` **or** `Ctrl+Alt+F` | Toggle fullscreen / windowed |
| `Ctrl+Alt+Q` | Shut down Nautilus |
| `Ctrl+Alt+Esc` | Minimize the shell to the system tray |
| `Ctrl+Alt+A` | Launch **Abyssal IDE** |
| `Ctrl+Alt+S` | Launch **Surfline Browser** |
| `Ctrl+Alt+R` | Launch **Riptide Audio** |
| `Ctrl+Alt+M` | Launch **Cinema** |
| `Ctrl+Alt+L` | Launch **Logbook** |
| `Ctrl+Alt+E` | Launch **Mariner** |
| `Ctrl+Alt+C` | Launch **Current Telemetry** |
| `Ctrl+Alt+H` | Launch **Harbor File Manager** |
| `Ctrl+Alt+T` | Launch **Tide Terminal** |
| `Ctrl+Alt+,` | Launch **Anchor Settings** |
| `Ctrl+Alt+K` | Launch **Kraken AI** |
| `Ctrl+Alt+Z` | Launch **Reef Messenger** |

---

## Applications

Every app is a standalone process with its own entry point. Run it from the
repository root with `python3 apps/<App>/main.py`, or launch it from the
desktop dock / grid / search. All apps reuse the Nautilus theme and bootstrap.

| App | Run | Shortcut | Notes |
| :--- | :--- | :--- | :--- |
| **Abyssal IDE** | `python3 apps/Abyssal/main.py` | `Ctrl+Alt+A` | Multi-language code editor, command palette, integrated terminal. |
| **Surfline Browser** | `python3 apps/Surfline/main.py` | `Ctrl+Alt+S` | WebKit/WebEngine browser, dark mode, password vault. Needs `cryptography`. |
| **Riptide Audio** | `python3 apps/RipTide/main.py` | `Ctrl+Alt+R` | Multi-provider audio + SFX soundboard. Needs `requests` + `pygame`. |
| **Cinema** | `python3 apps/Cinema/main.py` | `Ctrl+Alt+M` | Local-only media center; import your own movies/shows. |
| **Logbook** | `python3 apps/Logbook/main.py` | `Ctrl+Alt+L` | Markdown notes, live preview, full-text search. |
| **Mariner** | `python3 apps/Mariner/main.py` | `Ctrl+Alt+E` | Scientific calculator, history tape, nautical units. |
| **Current Telemetry** | `python3 apps/Current/main.py` | `Ctrl+Alt+C` | CPU/RAM/thermal monitor + process kill. Needs `psutil`. |
| **Harbor File Manager** | `python3 apps/Harbor/main.py` | `Ctrl+Alt+H` | Keyboard-first dual-pane file manager with previews. |
| **Tide Terminal** | `python3 apps/Tide/main.py` | `Ctrl+Alt+T` | Tabbed terminal with a **pure-Python internal shell** — no external `$SHELL` required. |
| **Anchor Settings** | `python3 apps/anchor/main.py` | `Ctrl+Alt+,` | Control center: display, network, audio, theme. |
| **Kraken AI** | `python3 apps/kraken/main.py` | `Ctrl+Alt+K` | Local-first AI chat + multi-agent workforce. See below. |
| **Reef Messenger** | `python3 apps/Reef/main.py` | `Ctrl+Alt+Z` | Local-first messenger; offline thread + optional IMAP/SMTP mail. |

> Apps self-locate the project root, so they also run from any working
> directory. `Surfline` accepts a URL as its first argument
> (`python3 apps/Surfline/main.py https://example.com`) and opens it as the
> initial tab — this is how the desktop search opens web results.

---

## Kraken AI — CLI & GUI

Kraken is a local-first agentic engine. The engine is **pure stdlib with zero
mandatory dependencies** — it just needs a reachable model server
(Ollama / LM Studio / vLLM / llama.cpp) or an OpenAI-compatible endpoint.

```sh
# Without installing:
python3 kraken.py models          # discovered local models + API keys
python3 kraken.py doctor          # health check and backend recommendation

# After `pip install .`:
kraken models
kraken setup                      # auto-configure the best backend found
kraken chat                       # interactive REPL
kraken-gui                        # or the PySide6 desktop app
```

API keys come from `~/.kraken/keys.json`, `~/.env`, or environment variables
(e.g. `OPENAI_API_KEY`) and are managed with:

```sh
kraken keys
kraken keys add openai sk-...
kraken keys remove openai
```

Custom agents are Markdown specs in `~/.kraken/agents/`:

```sh
kraken agent list
kraken agent new ReviewCritic --model qwen2.5-coder:7b --desc "Ruthless reviewer"
kraken agent run ReviewCritic "review the auth pipeline"
```

See `pyproject.toml` and `apps/kraken/` for the full CLI surface.

---

## Where Your Data Lives

| Location | Contents |
| :--- | :--- |
| `~/.kraken/` | Kraken config, API keys, agent specs, SQLite error-learning memory |
| `~/.reef/` | Reef messenger accounts (`accounts.json`) + messages (`messages.json`) |
| `~/.nautilus/search.json` | Global search engine choice + custom file-search roots |
| `~/Documents/Logbook/` | Logbook notes archive |
| `assets/logos/` | Pre-generated app logo PNGs (regenerated automatically) |

---

## Testing & Development

```sh
# Lint (ruff)
python3 -m ruff check .

# Smoke-test every app (launches each standalone, 4 s each)
python3 tests/smoke_test.py
python3 tests/smoke_test.py --app tide      # test a single app

# Kraken engine unit tests
python3 tests/test_kraken_engine.py
python3 tests/test_kraken_agents.py
python3 tests/test_kraken_providers.py
```

Headless / CI runs need a few extra env vars:

```sh
export QT_QPA_PLATFORM=offscreen
export SDL_AUDIODRIVER=dummy SDL_VIDEODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1
export QTWEBENGINE_DISABLE_SANDBOX=1
```

---

## Repository Structure

```text
nautilus/
├── core/                  # System: shell (main.py), launcher, theme, icons,
│                          #   search, search overlay, wallpaper, auth, logger
├── apps/
│   ├── Abyssal/           # Code editor & IDE
│   ├── Surfline/          # Web browser (WebEngine)
│   ├── RipTide/           # Audio hub + SFX board (pygame)
│   ├── Cinema/            # Local media center
│   ├── Logbook/           # Markdown notes
│   ├── Mariner/           # Calculator
│   ├── Current/           # System telemetry
│   ├── Harbor/            # File manager
│   ├── Tide/              # Terminal with internal shell
│   ├── anchor/            # Control center / settings
│   ├── kraken/            # Agentic AI engine (CLI + PySide6 GUI)
│   └── Reef/              # Messenger (offline thread + IMAP/SMTP)
├── agents/                # Example Kraken agent specs
├── kraken.py              # Kraken CLI shim (no install needed)
├── core/main.py           # Desktop shell entry point
├── requirements.txt       # All OS + app Python dependencies
├── pyproject.toml         # Kraken AI packaging (`pip install .`)
├── tests/                 # Smoke + unit tests
├── docs/                  # Architecture and PRDs
└── README.md
```

---

## Design Tokens

Nautilus ships one token set (`core/theme.py`) shared by the shell and every app.

| Token | Hex | Usage |
| :--- | :--- | :--- |
| Abyss Navy | `#081626` | Main window backdrops, root viewports |
| Slate Navy | `#0E2238` | Sidebars, toolbars, inactive panels |
| Seafoam | `#00F2C2` | Primary accent — carets, active borders, running dots |
| Coral | `#FF7F50` | Errors, warnings, shutdown |
| HD White | `#EEF4F8` | Primary text, mono fonts |

Shell surfaces use these tokens at reduced alpha over the ocean wallpaper to
create the glass effect; apps use them fully opaque with the industrial
zero-radius language of the global stylesheet.

---

*MIT License — see `LICENSE`.*
