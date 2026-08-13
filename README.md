# Nautilus: Technical Architecture & System Documentation

## Overview

Nautilus is a lightweight, low-overhead desktop ecosystem built specifically for low-resource hardware like the Raspberry Pi 500. It addresses system fragmentation and high RAM footprints caused by heavy desktop environments and Electron-based software. 

By employing a strict zero-border-radius design language (`border-radius: 0px`) and a monochromatic, high-contrast palette, Nautilus provides a fast, keyboard-centric interface optimized for software engineering, media production, and daily workflows.

---

## Technical Specifications

* **Primary Target System:** Raspberry Pi 500 (ARM64, 8GB RAM recommended)
* **Storage Requirement:** Minimum 16GB MicroSDXC Class 10 / UHS-I
* **Display Output:** Native 1080p (1920x1080) Full HD via Micro-HDMI to HDMI
* **UI Framework:** Python 3.11+ / PySide6 (Qt for Python)
* **Active Memory Base:** Under 350 MB total RAM footprint at system boot
* **Global Search:** Press `Ctrl+Space` from the desktop to search installed apps, local files, and the web — results open in apps or the Surfline browser. Offline-first: local results never touch the network.
* **Floating Glass Desktop:** Modern shell with a translucent glass top bar, centered glass dock (running-app dots), and a full-screen app grid (`Meta` or `Ctrl+Alt+G`) — all surfaces show the ocean wallpaper through them.

---

## Design System & Color Tokens

The visual design language relies on strict, industrial grid layouts with no soft shadows, gradients, or rounded corners.

* **Base Background (`#081626`):** Abyss Navy - Used for main window backdrops and root viewports.
* **Surface / Container (`#0E2238`):** Slate Navy - Used for sidebars, toolbars, and inactive panels.
* **Primary Accent (`#00F2C2`):** Seafoam - Used for text cursors, active borders, selection state, and primary indicators.
* **Warning / Alert (`#FF7F50`):** Coral - Used for error highlights, system notifications, and process warnings.
* **Secondary Text (`#EEF4F8`):** High-Density White - Used for all primary body text, mono fonts, and UI labels.

---

## System Architecture & Application Suite

The software suite in Nautilus consists of modular components designed to run as standalone native processes while sharing system design tokens and IPC (Inter-Process Communication) protocols.

| Application / Module | Primary Purpose | Key Features & Functional Requirements | Target Performance Metrics |
| :--- | :--- | :--- | :--- |
| **Abyssal** | Native Code Editor & IDE | Multi-language syntax parser (Python, C/C++, Shell, JSON), zero-delay caret response, integrated command palette (`Ctrl+Shift+P`), split-view subprocess terminal drawer (`F5` execution), and direct link to Surfline documentation lookups. | < 80 MB RAM usage, < 1.5s cold launch time |
| **Surfline** | Web Browser | WebKit/QtWebEngine core, low-overhead tab management, dark mode engine, integrated developer tools, and API integration with local documentation databases. | < 250 MB base RAM usage with 3 active tabs |
| **Riptide Audio** | Universal Audio & SFX Hub | Simultaneous OAuth 2.0 multi-account integration (Spotify, Apple Music, YouTube Music, SoundCloud), cross-platform mega-playlist engine, dynamic stream switching, and secondary-bus zero-latency SFX soundboard channel. | < 60 MB RAM usage, < 500ms audio stream handoff |
| **Current** | Telemetry & System Monitor | Real-time monitoring of CPU core frequencies, memory allocation breakdown, thermal throttling metrics, and process tree management with instant process termination signals (`SIGKILL`). | < 15 MB RAM usage, 1s refresh interval |
| **Harbor** | Keyboard-First File Manager | Dual-pane grid layout, instant file indexing, direct text/image/audio file previews, archive compression (`.tar.gz`, `.zip`), and root execution toggles. | < 30 MB RAM usage, < 100ms directory indexing |
| **Cinema** | Media Center | Local-only offline movie & TV library: import your own media, poster grid, continue-watching, and full-screen QtMultimedia playback. | < 180 MB RAM usage with player |
| **Logbook** | Notes & Documentation | Keyboard-first markdown notes with live rendered preview, instant full-text search, auto-save, and a naval logbook archive in `~/Documents/Logbook`. | < 40 MB RAM usage |
| **Mariner** | Scientific Calculator | Whitelisted expression evaluator (trig, logs, powers, factorial), persistent history tape, and nautical unit helpers. | < 20 MB RAM usage |
| **Tide** | GPU-Accelerated Terminal | Tabbed shell container, customizable keybindings, split pane arrangement, UTF-8 color support, and deep IPC hooks with Abyssal. | < 25 MB RAM usage, sub-millisecond input latency |
| **Anchor** | Control Center & System Settings | Display resolution and scaling controls, Wi-Fi / Bluetooth management, audio channel mixing, system updates, and global UI token configuration. | < 20 MB RAM usage |
| **Kraken AI** | Local-First Agentic Engine & Multi-Agent Workforce | Model-agnostic chat (Ollama / LM Studio / vLLM / llama.cpp), Markdown-driven agent specs (`kraken build --spec`), a SQLite error-learning loop, and an orchestrator/worker workforce for parallel engineering tasks. CLI (`kraken.py`) + PySide6 desktop app with a real-time workforce tree. | < 120 MB RAM usage |
| **Reef** | Messenger | Local-first messaging and mail: an offline local thread that always works, plus optional IMAP/SMTP accounts with credentials stored in `~/.reef`. | < 40 MB RAM usage |

---

## Repository Structure

```text
nautilus/
├── core/               # System launcher, window manager, theme tokens
├── apps/
│   ├── abyssal/        # Code Editor
│   ├── surfline/       # Web Browser
│   ├── riptide/        # Audio Hub
│   ├── current/        # System Monitor
│   ├── harbor/         # File Manager
│   ├── tide/           # Terminal Emulator
│   ├── cinema/         # Media Center
│   ├── logbook/        # Markdown Notes
│   ├── mariner/        # Calculator
│   ├── anchor/         # System Settings
│   └── kraken/         # Local-First Agentic AI Engine (CLI + PySide6)
├── agents/             # Example Markdown agent specs (Kraken)
├── kraken.py           # Kraken AI CLI entry point
├── docs/               # Architecture and PRDs
├── .gitignore          # Repository exclusions
├── requirements.txt    # Shared Python dependencies
pyproject.toml      # Kraken AI packaging (installable `kraken` CLI)
├── README.md           # System documentation
└── LICENSE             # MIT License

---

## Kraken AI — Installation

Kraken is packaged for pip. The engine itself is pure Python stdlib and has
**zero mandatory dependencies** — you only need a reachable local model server
(Ollama / LM Studio / vLLM / llama.cpp) or a custom OpenAI-compatible endpoint.

```sh
# Install the `kraken` CLI (works anywhere on your PATH)
pip install .

# Install the `kraken-gui` desktop app too (adds PySide6)
pip install ".[gui]"
```

Run it:


### Backends & API keys

Kraken talks to any local server (Ollama, LM Studio, vLLM, llama.cpp) and any
OpenAI-compatible cloud API — plus Anthropic's native API and Google Gemini.
It auto-discovers models that are already on your machine:

```sh
kraken models        # downloaded local models + detected API keys
kraken doctor        # health check: local servers, keys, recommended backend
kraken setup         # auto-configure the best backend it finds
```

API keys are resolved from `~/.kraken/keys.json` → `~/.env` → environment
variables (e.g. `OPENAI_API_KEY`), and can be managed with:

```sh
kraken keys                        # list detected keys (masked)
kraken keys add openai sk-...      # store a key (0600 file)
kraken keys remove openai          # drop it
```

Built-in cloud providers: `openai`, `anthropic`, `gemini`, `groq`,
`openrouter`, `mistral`, `deepseek`, `together`. Point `kraken config
provider/base_url/model` at anything else (OpenAI-compatible) with `custom`.

### Custom agents


Kraken has a **custom agent catalog** — Markdown agent specs stored in
`~/.kraken/agents/` that you can invoke by name from the CLI, the REPL, and
the desktop app's agent manager.

```sh
kraken agent list                                          # show the library
kraken agent new ReviewCritic --model qwen2.5-coder:7b \
    --desc "Ruthless code reviewer"                        # scaffold an agent
kraken agent show ReviewCritic                             # inspect it
kraken agent edit ReviewCritic                             # open in $EDITOR
kraken agent import ./agents/DatabaseArchitect.md          # copy a spec in
kraken agent run ReviewCritic "review the auth pipeline"   # run it on a task
kraken agent run ReviewCritic "task" --agent-mode          # ... as a workforce
kraken --spec ReviewCritic "review the auth pipeline"      # or load by name
kraken agent remove ReviewCritic                           # delete (--force skips prompt)
```

A spec can also declare workforce roles, a default mode, and a context
window, so custom agents can take over roles inside Agent Mode:

```markdown
---
name: DevPlanner
model: qwen2.5-coder:32b
tools: [file_read, file_write, file_list]
workforce_roles: [planner, qa]   # this agent serves these roles
default_mode: agent               # auto-enable agent mode
num_ctx: 32768
system_prompt: You are the planning brain. Output only a task list.
---
```

In the REPL, `/agents` lists the library and `/spec <name>` loads an agent by
name or path.
Example agent specs ship to `<venv>/share/kraken/agents/`. Config, the
SQLite error-learning memory, and specs live in `~/.kraken/`.
