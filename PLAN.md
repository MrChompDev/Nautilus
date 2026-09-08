# Nautilus OS — Full Expansion Plan

> Transform from a basic desktop shell into a **cybersecurity powerhouse**
> with gamified tools, completed apps, and a game arcade.

---

## Architecture Overview

### New Core Modules

```
core/
├── main.py              # Shell (updated dock, new apps)
├── theme.py             # Design tokens (updated with new colors)
├── profile.py           # 🆕 Gamification: coins, XP, achievements, levels
├── tutorials.py         # 🆕 Tutorial engine: step-by-step guides per tool
└── launcher.py          # 🆕 App registry (replaces hardcoded if/elif)
```

### Gamification System (`core/profile.py`)

**Storage:** `~/.nautilus/profile.json`

```json
{
  "version": 1,
  "username": "Crewmate",
  "level": 1,
  "xp": 0,
  "coins": 0,
  "achievements": [],
  "completed_tutorials": [],
  "tool_stats": {
    "port_scanner": { "uses": 0, "best_scan": null }
  }
}
```

**XP & Leveling:**
- Earn XP by: completing tutorials (+50 XP), running tools (+10 XP), completing challenges (+100 XP), finding secrets (+25 XP)
- Level formula: `level = floor(sqrt(xp / 50))`
- Each level shows in TopBar: `⚓ Level 5 | 🪙 340 coins`

**Coin Economy:**
- Earn coins by: completing tutorials (+25 coins), running tools (+5 coins), challenges (+50 coins)
- Spend coins on: theme skins, dock icon packs, tool customizations
- Coin display in TopBar next to level

**Achievements (examples):**
- `first_scan` — "Reef Walker" — Run your first port scan
- `first_breach` — "Hull Breach" — Complete your first red team challenge
- `firewall_master` — "Sea Wall" — Configure 5 firewall rules
- `full_outerve` — "Deep Dive" — Complete all recon tools
- `arcade_champion` — "Arcade Captain" — Beat high scores on 5 games

### Theme Updates (`core/theme.py`)

Add new color tokens for gamification and cybersec:

```python
COLORS.update({
    # Gamification
    "gold":        "#FFD700",
    "gold_dim":    "#B8960F",
    "xp_blue":     "#4FC3F7",

    # Cybersec status
    "scan_green":  "#00E676",
    "alert_red":   "#FF1744",
    "stealth":     "#7C4DFF",
    "warning_alt": "#FF9100",

    # Arcade
    "arcade_pink": "#FF4081",
    "arcade_cyan": "#00E5FF",
})
```

### App Registry (`core/launcher.py`)

Replace hardcoded `launch_app` if/elif with a manifest:

```python
APP_MANIFEST = {
    "Surfline":  {"module": "apps.surfline.app",  "class": "SurflineWindow",  "icon": "jellyfish.svg"},
    "Abyssal":   {"module": "apps.abyssal.app",    "class": "AbyssalWindow",   "icon": "anglerfish.svg"},
    "Kraken":    {"module": "apps.kraken.app",     "class": "KrakenWindow",    "icon": "octopus.svg"},
    "Logbook":   {"module": "apps.logbook.app",    "class": "LogbookWindow",   "icon": "turtle.svg"},
    "Trench":    {"module": "apps.trench.app",     "class": "TrenchWindow",    "icon": "narwhal.svg"},
    "Manta":     {"module": "apps.manta.app",      "class": "MantaWindow",     "icon": "manta.svg"},
    "Coral":     {"module": "apps.coral.app",      "class": "CoralWindow",     "icon": "crab.svg"},
    "Drift":     {"module": "apps.drift.app",      "class": "DriftWindow",     "icon": "seahorse.svg"},
    "Depths":    {"module": "apps.depths.app",     "class": "DepthsWindow",    "icon": "depths.svg"},
    "Arcade":    {"module": "apps.arcade.app",     "class": "ArcadeWindow",    "icon": "arcade.svg"},
    "Mariner":   {"module": "apps.mariner.app",    "class": "MarinerWindow",   "icon": "mariner.svg"},
    "Tide":      {"module": "apps.tide.app",       "class": "TideWindow",      "icon": "tide.svg"},
    "Harbor":    {"module": "apps.harbor.app",     "class": "HarborWindow",    "icon": "harbor.svg"},
    "Current":   {"module": "apps.current.app",    "class": "CurrentWindow",   "icon": "current.svg"},
    "Anchor":    {"module": "apps.anchor.app",     "class": "AnchorWindow",    "icon": "anchor.svg"},
    "Riptide":   {"module": "apps.riptide.app",    "class": "RiptideWindow",   "icon": "riptide.svg"},
}
```

---

## App Completion Plan

### Phase 1 — Core Apps (Build First)

#### 1. Abyssal — Code Editor
**Files:** `apps/abyssal/app.py`, `editor.py`, `sidebar.py`, `tabs.py`, `minibar.py`

| Feature | Detail |
|---------|--------|
| Syntax highlighting | QSyntaxHighlighter for Python, JS, HTML, CSS, JSON, MD |
| File tree sidebar | QTreeView + QFileSystemModel, collapsible |
| Tab system | One editor per tab, closeable, unsaved indicator |
| Minibar | Line:Col indicator, language label, encoding |
| Find/replace | Ctrl+F bar, regex support |
| Theme | Tokens only, dark-on-dark matching shell |
| Extensions | Plugin folder `apps/abyssal/plugins/`, load `.py` files that register menu items |
| Standalone | `python3 apps/abyssal/main.py` |

#### 2. Logbook — Markdown Notes (Obsidian-inspired)
**Files:** `apps/logbook/app.py`, `editor.py`, `preview.py`, `sidebar.py`, `search.py`

| Feature | Detail |
|---------|--------|
| Split pane | Left: file list, Center: editor, Right: live HTML preview |
| Markdown | Python-Markdown or custom renderer for bold/italic/links/code/headers |
| Note storage | `~/Documents/Logbook/` as flat `.md` files |
| Full-text search | QTextEdit.find() across all notes |
| Tags | Parse `#tag` from content, filterable sidebar |
| Backlinks | Simple grep-based "linked mentions" panel |
| Extensions | Plugin folder, same pattern as Abyssal |
| Standalone | `python3 apps/logbook/main.py` |

#### 3. Trench — Document Editor (Word-like)
**Files:** `apps/trench/app.py`, `editor.py`, `toolbar.py`, `sidebar.py`

| Feature | Detail |
|---------|--------|
| Rich text | QTextEdit with HTML backend, format toolbar |
| Toolbar | Bold, italic, underline, strikethrough, headings, lists, alignment, font size |
| File format | Save/load `.html` and `.txt` |
| Page view | Optional print-preview style centered page |
| Find/replace | Ctrl+F bar |
| Word count | Status bar word/char/line count |
| Standalone | `python3 apps/trench/main.py` |

#### 4. Coral — Spreadsheets (Excel-like)
**Files:** `apps/coral/app.py`, `grid.py`, `formula_bar.py`, `toolbar.py`

| Feature | Detail |
|---------|--------|
| Grid | QTableWidget, 1000x26 columns, resizable |
| Cell editing | Click-to-edit, formula bar sync |
| Formulas | Simple eval: `=SUM(A1:A10)`, `=AVG()`, `=MIN()`, `=MAX()`, `=COUNT()` |
| Formatting | Bold, colors, alignment via toolbar |
| CSV import/export | File > Open CSV, File > Save CSV |
| Multiple sheets | Tab bar at bottom, add/rename/delete sheets |
| Standalone | `python3 apps/coral/main.py` |

#### 5. Manta — Presentation Builder (PowerPoint-like)
**Files:** `apps/manta/app.py`, `slides.py`, `editor.py`, `toolbar.py`

| Feature | Detail |
|---------|--------|
| Slide list | Left sidebar, thumbnail previews |
| Slide editor | Center canvas, click-to-add text/image/shapes |
| Toolbar | Text formatting, backgrounds, layouts |
| Slide types | Title, content, two-column, image-focus |
| Presentation mode | F11 fullscreen slideshow with arrow-key navigation |
| Export | Save as `.html` slideshow |
| Standalone | `python3 apps/manta/main.py` |

#### 6. Drift — Email Client
**Files:** `apps/drift/app.py`, `viewer.py`, `composer.py`, `sidebar.py`

| Feature | Detail |
|---------|--------|
| IMAP/POP3 | Connect to any email provider (Gmail, Outlook, etc.) |
| SMTP send | Compose and send emails |
| Inbox view | QTableWidget with sender, subject, date columns |
| Reading pane | Right side HTML email viewer |
| Compose | Popup window with To, Subject, Body, Attach |
| Accounts | Multiple account support, stored in vault |
| Standalone | `python3 apps/drift/main.py` |

### Phase 2 — Utility Apps

#### 7. Mariner — Scientific Calculator
**Files:** `apps/mariner/app.py`, `engine.py`

| Feature | Detail |
|---------|--------|
| Expression eval | Safe eval with whitelist (math functions only) |
| Display | Large result + expression history tape |
| Buttons | 0-9, ops, sin/cos/tan/log/sqrt/pi/e, memory M+/M-/MR |
| History | Scrollable history panel |
| Units | Nautical: kn, nm, ftm + standard: °C/°F, m/ft |
| Standalone | `python3 apps/mariner/main.py` |

#### 8. Tide — Terminal Emulator
**Files:** `apps/tide/app.py`, `shell.py`, `tabs.py`

| Feature | Detail |
|---------|--------|
| Internal shell | Pure-Python builtins: cd, pwd, ls, cat, echo, mkdir, rm, cp, mv, env, history |
| Real shell passthrough | Falls back to `$SHELL` for unknown commands |
| Tabbed sessions | One terminal per tab, add/close |
| Copy/paste | Ctrl+Shift+C/V |
| Font size | Ctrl+Plus/Minus |
| ANSI colors | Parse and render basic ANSI escape codes |
| Standalone | `python3 apps/tide/main.py` |

#### 9. Harbor — File Manager
**Files:** `apps/harbor/app.py`, `tree.py`, `preview.py`

| Feature | Detail |
|---------|--------|
| Dual panes | Left/right directory panels |
| Navigation | Breadcrumb bar, keyboard-first (Enter to open, Backspace to go up) |
| Operations | Copy, move, delete, rename via right-click menu |
| Previews | Image/text/file-size preview pane |
| Hidden files | Toggle with Ctrl+H |
| Bookmarks | Sidebar with pinned folders |
| Standalone | `python3 apps/harbor/main.py` |

#### 10. Current — System Monitor
**Files:** `apps/current/app.py`, `charts.py`, `processes.py`

| Feature | Detail |
|---------|--------|
| CPU/RAM graphs | Live updating line charts ( QPainter) |
| Process table | QTableWidget: PID, name, CPU%, RAM, status |
| Kill button | Select process → Kill (SIGTERM) |
| Thermal | CPU temperature if available (psutil) |
| Disk usage | Partition usage bars |
| Network | Upload/download bytes per second |
| Standalone | `python3 apps/current/main.py` |

#### 11. Anchor — Settings Hub
**Files:** `apps/anchor/app.py`, `themes.py`, `profiles.py`

| Feature | Detail |
|---------|--------|
| Display | Resolution, orientation |
| Network | WiFi status, IP address |
| Theme viewer | Browse/edit tokens, live preview |
| User profile | Edit username, avatar, level display |
| About | Nautilus OS version, credits, licenses |
| Storage | Read/write `~/.nautilus/settings.json` |
| Standalone | `python3 apps/anchor/main.py` |

#### 12. Riptide — Music Player
**Files:** `apps/riptide/app.py`, `player.py`, `playlist.py`, `visualizer.py`

| Feature | Detail |
|---------|--------|
| Library scan | Scan folder for .mp3/.wav/.ogg files |
| Playback | pygame.mixer for audio |
| Controls | Play/pause, next/prev, seek bar, volume |
| Playlist | Drag-reorder queue |
| Visualizer | Simple waveform or bar visualizer (QPainter) |
| Now playing | Album art area, track info |
| Standalone | `python3 apps/riptide/main.py` |

---

## 🆕 The Depths — Cybersecurity Hub

**Dock icon:** `depths.svg` (new — deep-sea diver helmet)

This is the **main cybersec app** — a category browser that launches individual tools.

### Architecture

```
apps/depths/
├── __init__.py
├── app.py              # DepthsWindow — main hub with category tabs
├── hub.py              # Category cards, tool launcher
├── tutorial_engine.py  # Tutorial overlay system
├── coin_display.py     # Coin/XP bar in tool windows
├── tools/
│   ├── __init__.py
│   ├── port_scanner.py       # 🔵 Recon
│   ├── network_map.py        # 🔵 Recon
│   ├── whois_lookup.py       # 🔵 Recon
│   ├── dns_enum.py           # 🔵 Recon
│   ├── subdomain_finder.py   # 🔵 Recon
│   ├── packet_capture.py     # 🔵 Recon
│   ├── vuln_scanner.py       # 🔴 Red Team
│   ├── password_cracker.py   # 🔴 Red Team
│   ├── sql_injector.py       # 🔴 Red Team
│   ├── exploit_builder.py    # 🔴 Red Team
│   ├── hash_analyzer.py      # 🔴 Red Team
│   ├── payload_craft.py      # 🔴 Red Team
│   ├── log_analyzer.py       # 🟢 Blue Team
│   ├── firewall_manager.py   # 🟢 Blue Team
│   ├── incident_responder.py # 🟢 Blue Team
│   ├── threat_hunter.py      # 🟢 Blue Team
│   ├── malware_sandbox.py    # 🟢 Blue Team
│   ├── memory_forensics.py   # 🟣 Forensics
│   ├── disk_analyzer.py      # 🟣 Forensics
│   ├── steganography.py      # 🟣 Forensics
│   ├── timeline_builder.py   # 🟣 Forensics
│   ├── cipher_challenges.py  # ⚪ Crypto
│   ├── hash_cracker.py       # ⚪ Crypto
│   ├── caesar_wheel.py       # ⚪ Crypto
│   ├── rsa_playground.py     # ⚪ Crypto
│   ├── osint_recon.py        # 🔵 OSINT
│   ├── social_mapper.py      # 🔵 OSINT
│   ├── wifi_analyzer.py      # 🔵 Wireless
│   └── packet_injector.py    # 🔵 Wireless
```

### Hub UI (`apps/depths/app.py`)

```
┌─────────────────────────────────────────────────┐
│ 🪙 340  ⚓ Level 5  │  The Depths              │
├─────────────────────────────────────────────────┤
│  [Recon] [Red Team] [Blue Team] [Forensics]    │
│  [Crypto] [OSINT] [Wireless] [Challenges]      │
├─────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 🔍 Port  │ │ 🗺️ Net   │ │ 📡 DNS   │        │
│  │ Scanner  │ │ Map      │ │ Enum     │        │
│  │ ⭐⭐⭐   │ │ ⭐⭐     │ │ ⭐       │        │
│  │ 🪙 120   │ │ 🪙 85    │ │ 🪙 60    │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 🔎 WHOIS │ │ 🌐 Sub-  │ │ 📦 Pkt   │        │
│  │ Lookup   │ │ domain   │ │ Capture  │        │
│  │ ⭐⭐     │ │ ⭐⭐⭐   │ │ ⭐⭐⭐⭐ │        │
│  │ 🪙 70    │ │ 🪙 150   │ │ 🪙 200   │        │
│  └──────────┘ └──────────┘ └──────────┘        │
├─────────────────────────────────────────────────┤
│  Tutorial available: "Port Scanning 101"        │
│  [Start Tutorial]  [Free Play]                  │
└─────────────────────────────────────────────────┘
```

### Tool Categories & Individual Tools

#### 🔵 Reconnaissance (Ocean Recon)

| Tool | What It Does | Tutorial | Challenge |
|------|-------------|----------|-----------|
| **Port Scanner** | TCP connect scan on target host, shows open ports/services | "Port Scanning 101" — scan localhost | Scan a "mystery server" to earn coins |
| **Network Map** | Discover hosts on local subnet, show topology | "Mapping Your Waters" — discover 5 devices | Find the hidden device |
| **WHOIS Lookup** | Query domain registration info | "Domain Detective" — look up a domain | Identify the registrar of a challenge domain |
| **DNS Enumerator** | Query A, AAAA, MX, NS, TXT records for a domain | "DNS Depths" — enumerate records | Find the hidden TXT record |
| **Subdomain Finder** | Brute-force subdomain discovery | "Submarine Hunt" — find subdomains | Find all 5 hidden subdomains |
| **Packet Capture** | Capture and display network packets (scapy) | "Fishing for Packets" — capture 10 packets | Identify the malicious packet |

#### 🔴 Red Team (Predator Operations)

| Tool | What It Does | Tutorial | Challenge |
|------|-------------|----------|-----------|
| **Vuln Scanner** | Check target for common vulnerabilities | "Finding Cracks" — scan a test target | Find all 3 vulns in the challenge |
| **Password Cracker** | Dictionary/brute-force password testing | "Breaking the Lock" — crack a simple hash | Crack the challenge hash fastest |
| **SQL Injector** | Test URLs for SQL injection points | "Injecting the Current" — test a form | Exploit the blind SQLi challenge |
| **Exploit Builder** | Construct simple buffer overflow payloads | "Forging Harpoons" — build a basic payload | Build the correct payload |
| **Hash Analyzer** | Identify hash type, attempt rainbow table lookup | "Fingerprinting" — identify 5 hash types | Identify the mystery hash |
| **Payload Crafter** | Generate reverse shell payloads | "CraftingProjectiles" — create a payload | Match the correct payload type |

#### 🟢 Blue Team (Defender Operations)

| Tool | What It Does | Tutorial | Challenge |
|------|-------------|----------|-----------|
| **Log Analyzer** | Parse auth/sys logs, flag suspicious entries | "Reading the Wake" — find 3 anomalies | Detect the intrusion in logs |
| **Firewall Manager** | Create/view/modify iptables-style rules | "Building the Hull" — add 5 rules | Block all attack vectors |
| **Incident Responder** | Step-by-step IR checklist with scoring | "Man Overboard" — follow the IR process | Complete IR under time pressure |
| **Threat Hunter** | Search for IOCs (indicators of compromise) | "Hunting in the Deep" — find 5 IOCs | Hunt down the APT |
| **Malware Sandbox** | Analyze suspicious files (entropy, strings, imports) | "Dissecting the Jellyfish" — analyze a sample | Identify the malware family |

#### 🟣 Forensics (Deep Sea Forensics)

| Tool | What It Does | Tutorial | Challenge |
|------|-------------|----------|-----------|
| **Memory Forensics** | Parse memory dumps for processes, strings, artifacts | "Memory Dredge" — extract 3 artifacts | Find the hidden process |
| **Disk Analyzer** | Examine disk images, recover deleted files | "Seafloor Scan" — recover a deleted file | Recover the flag from the image |
| **Steganography** | Hide/extract messages in images | "Message in a Bottle" — embed & extract | Decode the steganographic flag |
| **Timeline Builder** | Construct event timelines from artifacts | "Tracing the Wake" — build a timeline | Reconstruct the attack timeline |

#### ⚪ Crypto Challenges (The Vault)

| Tool | What It Does | Tutorial | Challenge |
|------|-------------|----------|-----------|
| **Cipher Challenges** | Rot13, Base64, XOR, Atbash, Vigenere | "The Codebook" — decode 5 ciphers | Solve the multi-layer cipher |
| **Hash Cracker** | Brute-force short passwords against hash | "Breaking the Seal" — crack a hash | Crack the challenge hash |
| **Caesar Wheel** | Interactive Caesar cipher decoder | "Shifting Tides" — decode a message | Decode the mystery message |
| **RSA Playground** | Generate keys, encrypt/decrypt, understand the math | "Public & Private Keys" — generate a keypair | Decrypt the intercepted message |

#### 🔵 OSINT (Open Waters Intelligence)

| Tool | What It Does | Tutorial | Challenge |
|------|-------------|----------|-----------|
| **OSINT Recon** | Aggregate public info about a target | "Surface Search" — research a username | Find the hidden profile |
| **Social Mapper** | Map social media accounts by username | "Crossing Currents" — track one identity | Connect the 3 profiles |

#### 🔵 Wireless (Signal Depths)

| Tool | What It Does | Tutorial | Challenge |
|------|-------------|----------|-----------|
| **WiFi Analyzer** | Scan/display nearby networks, signal strength | "Reading the Waves" — scan networks | Identify the rogue AP |
| **Packet Injector** | Craft and inject custom packets | "Riding the Current" — send a test packet | Craft the correct deauth frame |

### Tutorial System (`core/tutorials.py`)

Each tool has a tutorial mode:

```
┌─────────────────────────────────────────────────┐
│ Tutorial: Port Scanning 101                      │
├─────────────────────────────────────────────────┤
│ Step 1/5                                        │
│                                                 │
│ A port scanner checks which ports on a target   │
│ are open and accepting connections. This is     │
│ the first step in reconnaissance.               │
│                                                 │
│ Think of it like knocking on every door of a    │
│ ship to see which ones are unlocked.            │
│                                                 │
│ [Next Step →]                                   │
├─────────────────────────────────────────────────┤
│ Progress: ████░░░░░░ 1/5        🪙 +50 XP      │
└─────────────────────────────────────────────────┘
```

- Step-by-step overlays within each tool
- Each completed tutorial: +50 XP, +25 coins
- Progress saved to profile
- "Tutorial Complete" badge on tool card in hub

### Challenge System

Each tool has a challenge mode:
- Pre-defined scenarios with known solutions
- Timed challenges for bonus coins
- Difficulty tiers: ⭐ (Beginner) → ⭐⭐⭐⭐⭐ (Expert)
- Leaderboard (local, stored in profile)
- Challenge completion: +100 XP, +50 coins

### Coin Rewards Table

| Action | Coins | XP |
|--------|-------|-----|
| Complete a tutorial | +25 | +50 |
| Run a tool (free play) | +5 | +10 |
| Complete a challenge (1 star) | +20 | +50 |
| Complete a challenge (3 stars) | +50 | +100 |
| Complete a challenge (5 stars) | +100 | +200 |
| Find a secret/easter egg | +25 | +25 |
| Daily login streak | +10 | +20 |

---

## 🆕 Arcade — Game Hub

**Dock icon:** `arcade.svg` (new — arcade cabinet)

### Architecture

```
apps/arcade/
├── __init__.py
├── app.py              # ArcadeWindow — game catalog grid
├── launcher.py         # Subprocess game launcher
├── catalog.py          # Game metadata (title, genre, rating, source)
└── player.py           # Game card widget with play button
```

### Arcade UI

```
┌─────────────────────────────────────────────────┐
│ 🕹️ The Arcade                          🪙 340   │
├─────────────────────────────────────────────────┤
│  [All] [Platformer] [Puzzle] [Action] [Sim]     │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌────────────┐│
│  │ 🎮 Slicker  │ │ 🎮 Trusty   │ │ 🎮 Slime   ││
│  │ Platformer  │ │ Platformer  │ │ Bound      ││
│  │ ⭐⭐⭐⭐⭐ │ │ ⭐⭐⭐⭐⭐ │ │ Puzzle     ││
│  │ 🪙 +10/play │ │ 🪙 +10/play │ │ ⭐⭐⭐⭐   ││
│  │ [PLAY]      │ │ [PLAY]      │ │ [PLAY]     ││
│  └─────────────┘ └─────────────┘ └────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌────────────┐│
│  │ 🎮 Dino     │ │ 🎮 Control  │ │ 🎮 Factory ││
│  │ Dinner      │ │ the Hoard   │ │ Escape     ││
│  │ Simulation  │ │ Action      │ │ Platformer ││
│  │ ⭐⭐⭐⭐   │ │ ⭐⭐⭐⭐⭐ │ │ ⭐⭐⭐⭐   ││
│  │ [PLAY]      │ │ [PLAY]      │ │ [PLAY]     ││
│  └─────────────┘ └─────────────┘ └────────────┘│
└─────────────────────────────────────────────────┘
```

### Game Catalog

All games launch via `subprocess.Popen([sys.executable, entry_point])`.

| # | Game | Genre | Source Path | Lines | Coins/Play |
|---|------|-------|-------------|-------|------------|
| 1 | **Slicker** | Platformer | `Games/Slicker/main.py` | 1,827 | +10 |
| 2 | **Trusty.exe** | Platformer | `Games/Game Jam/Trusty.exe/main.py` | 3,689 | +10 |
| 3 | **SlimeBound** | Puzzle | `Games/Game Jam/SlimeBound/main.py` | 2,083 | +10 |
| 4 | **Factory Escape** | Platformer | `Games/Game Jam/BlackThornProd/FactoryEscape/main.py` | 3,305 | +10 |
| 5 | **Fish & Fibs** | Simulation | `Games/Game Jam/Fish & Fibs/main.py` | 1,985 | +10 |
| 6 | **Control the Hoard** | Action | `Games/Game Jam/Control/main.py` | 3,101 | +10 |
| 7 | **Dino Dinner** | Simulation | `Games/Game Jam/Dino Dinner/main.py` | 2,868 | +10 |
| 8 | **UnBoxed** | Platformer | `Games/Game Jam/UNBOXED/main.py` | 2,983 | +10 |
| 9 | **FlowState** | Platformer | `Games/Game Jam/FlowState/main.py` | 1,572 | +10 |
| 10 | **The Longest Winter** | Adventure | `Games/Game Jam/Longest Winter/main.py` | 2,615 | +10 |
| 11 | **Neon Bastion** | Strategy | `Games/Game Jam/Neon Bastion/Scripts/main.py` | 1,938 | +10 |
| 12 | **HexBound** | Puzzle | `Games/Game Jam/HexBound/main.py` | 1,502 | +10 |
| 13 | **Bombs Galore** | Puzzle | `Games/Game Jam/Oops! All Bombs/main.py` | 1,491 | +10 |
| 14 | **ICECAPER** | Puzzle | `Games/Game Jam/ICECAPER/main.py` | 2,451 | +10 |
| 15 | **Surfers Paradise** | Rhythm | `Games/Game Jam/Surfers Paradise/scripts/surfers_paradise.py` | 1,095 | +10 |
| 16 | **DeckDive** | Fighting | `Games/DeckDive/deckdive_ultimate.py` | 2,882 | +10 |
| 17 | **Black Fin Protocol** | Platformer | `Games/Black Fin Protocol/main.py` | 2,221 | +10 |
| 18 | **FrostFall** | Platformer | `Games/FrostFall/frostfall.py` | 1,496 | +10 |
| 19 | **LCD CyberVerse** | Roguelike | `Games/LCD CyberVerse/Scripts/main.py` | 10,745 | +15 |
| 20 | **SharkSkin** | Action | `Games/SharkSkin/Scripts/main.py` | 4,606 | +15 |
| 21 | **Ocean's Wrath** | Action-Adventure | `Games/ocean_wrath/main.py` | 2,758 | +10 |
| 22 | **EchoBound** | Platformer | `Games/EchoBound/code/main.py` | 618 | +5 |
| 23 | **FNAF Game** | Horror | `Games/FNAF Game/code/main.py` | 1,483 | +10 |
| 24 | **Slicker Web** | Platformer | `Games/SlickerHTML/index.html` (QWebEngineView) | N/A | +10 |

### Launcher Implementation

```python
import subprocess, sys, os

GAMES_ROOT = "/run/media/danielb/DNB/Games"

def launch_game(entry_point, cwd=None):
    """Launch a Pygame game as a subprocess."""
    path = os.path.join(GAMES_ROOT, entry_point)
    subprocess.Popen(
        [sys.executable, path],
        cwd=cwd or os.path.dirname(path),
    )
```

Games run in their own window. Arcade tracks launch count for coin rewards.

### Arcade Coin Rewards

| Action | Coins |
|--------|-------|
| Launch any game | +5 |
| Launch a game for the first time | +10 |
| Play 5 different games in one session | +25 (achievement: "Game Hopper") |
| Play all 24 games | +100 (achievement: "Arcade Legend") |

---

## Dock Update

The dock needs to accommodate new apps. Two options:

**Option A: Expanded dock (12 buttons)**
```
[Surfline] [Abyssal] [Kraken] [Logbook] [Trench] [Manta] [Coral] [Drift] [Depths] [Arcade] [Tide] [Current]
```

**Option B: Scrollable dock (keep 8 visible, scroll for more)**
- Arrow buttons on sides to scroll through app list

**Option C: Two-row dock**
- Row 1: Core apps (8)
- Row 2: Tools & extras (8)

Recommendation: **Option A** — widen the dock to 12 buttons (wider window or smaller icons). The remaining apps (Mariner, Harbor, Anchor, Riptide) can be launched from a right-click desktop menu or app grid (Ctrl+Space).

New dock icons needed (SVG):
- `depths.svg` — Deep-sea diver helmet (cybersec hub)
- `arcade.svg` — Arcade cabinet
- `tide.svg` — Wave/terminal
- `current.svg` — Lightning bolt (system monitor)

---

## Implementation Order

### Wave 1 — Foundation (Do First)
1. `core/profile.py` — Gamification system
2. `core/launcher.py` — App registry
3. `core/tutorials.py` — Tutorial engine
4. Update `core/theme.py` — Add new color tokens
5. Update `core/main.py` — Use launcher, show coins/level in TopBar, expand dock

### Wave 2 — Cybersec Hub
6. `apps/depths/app.py` — Hub UI with categories
7. `apps/depths/hub.py` — Tool cards, launch system
8. `apps/depths/tutorial_engine.py` — Tutorial overlays
9. `apps/depths/coin_display.py` — Coin bar widget
10. Recon tools (6 tools)
11. Red Team tools (6 tools)
12. Blue Team tools (5 tools)
13. Forensics tools (4 tools)
14. Crypto tools (4 tools)
15. OSINT tools (2 tools)
16. Wireless tools (2 tools)

### Wave 3 — Core App Completion
17. Abyssal — Code editor
18. Logbook — Markdown notes
19. Trench — Document editor
20. Coral — Spreadsheets
21. Manta — Presentations
22. Drift — Email client

### Wave 4 — Utility Apps
23. Mariner — Calculator
24. Tide — Terminal
25. Harbor — File manager
26. Current — System monitor
27. Anchor — Settings
28. Riptide — Music player

### Wave 5 — Arcade
29. `apps/arcade/app.py` — Catalog UI
30. `apps/arcade/launcher.py` — Subprocess launcher
31. `apps/arcade/catalog.py` — Game metadata
32. Test all 24 games launch correctly

### Wave 6 — Polish
33. Update `requirements.txt` — Add all new deps
34. Create new SVG icons for dock
35. Write tests for core modules
36. Update wiki/README

---

## New Dependencies

```
# Already in requirements.txt
PySide6>=6.5.0
psutil>=5.9.0
cryptography>=42.0
requests>=2.31.0
pygame>=2.5.0

# New for cybersec tools
scapy>=2.5.0          # Packet capture/injection
python-whois>=0.9.4   # WHOIS lookups
dnspython>=2.6.0      # DNS enumeration
beautifulsoup4>=4.12  # HTML parsing (OSINT, web scraping)
markdown>=3.6         # Logbook markdown rendering

# Already in requirements but missing from surfline search.py
# (surfline/search.py uses requests + bs4 but they weren't listed)
```

---

## File Count Summary

| Category | New Files | Modified Files |
|----------|-----------|----------------|
| Core modules | 3 (`profile.py`, `launcher.py`, `tutorials.py`) | 3 (`main.py`, `theme.py`, `requirements.txt`) |
| Depths (cybersec) | ~35 files | — |
| App completions | ~20 files | 7 (placeholder app.py rewrites) |
| Utility apps | ~15 files | — |
| Arcade | 4 files | — |
| Assets (icons) | 4 new SVGs | — |
| **Total** | **~81 new files** | **~10 modified** |

---

## Total Tool/Game Count

- **Cybersecurity tools:** 29 individual tools across 6 categories
- **Games in arcade:** 24 playable games
- **Completed apps:** 8 (Abyssal, Logbook, Trench, Coral, Manta, Drift, Mariner, Tide)
- **System apps:** 4 (Harbor, Current, Anchor, Riptide)
- **Hub apps:** 2 (Depths, Arcade)
- **Total dock apps:** 12 core + launch-from-menu for the rest
