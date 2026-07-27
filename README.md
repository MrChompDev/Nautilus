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
| **Tide** | GPU-Accelerated Terminal | Tabbed shell container, customizable keybindings, split pane arrangement, UTF-8 color support, and deep IPC hooks with Abyssal. | < 25 MB RAM usage, sub-millisecond input latency |
| **Anchor** | Control Center & System Settings | Display resolution and scaling controls, Wi-Fi / Bluetooth management, audio channel mixing, system updates, and global UI token configuration. | < 20 MB RAM usage |

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
│   └── anchor/         # System Settings
├── docs/               # Architecture and PRDs
├── .gitignore          # Repository exclusions
├── requirements.txt    # Shared Python dependencies
├── README.md           # System documentation
└── LICENSE             # MIT License
