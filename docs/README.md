# Nautilus OS

A lightweight, ocean-inspired desktop ecosystem built for performance on low-spec hardware like the Raspberry Pi 500. Featuring a high-density, zero-radius dark UI, it packages native tools including Surfline (browser), Abyssal (code editor), Riptide (audio hub), Current (system monitor), and Harbor (keyboard-first file manager).

---

## Architecture Overview

Chomp OS replaces resource-heavy desktop environments with a native, highly integrated workspace. All core applications are constructed using Python and PySide6 to enforce a unified aesthetic and minimal memory footprint.

### System Palette
- **Deep Navy (`#081626`):** Primary window background.
- **Slate Navy (`#0E2238`):** Panels, sidebars, and inactive inputs.
- **Seafoam (`#00F2C2`):** Active selections, focus lines, and caret indicators.
- **Coral (`#FF7F50`):** Alerts, error indicators, and break points.
- **Geometry:** 0px border-radius across all windows, inputs, buttons, and popovers.

---

## Installed Applications & Components

| Component | Type | Description |
| :--- | :--- | :--- |
| **Abyssal** | Application | Native IDE with built-in subprocess terminal drawer and lexical syntax parser. |
| **Surfline** | Application | High-density WebKit-based web browser optimized for low memory usage. |
| **Riptide Audio** | Application | Multi-provider streaming aggregator and SFX soundboard player. |
| **Current** | Utility | Real-time hardware performance, thermal, and process monitoring tool. |
| **Harbor** | Utility | Dual-pane keyboard-driven file system manager with live asset previews. |
| **Tide** | Utility | Fast, split-pane terminal emulator with native shell support. |
| **Anchor** | System | System preferences manager for networking, display, and theme configs. |

---

## Hardware Requirements

- **Processor:** Broadcom BCM2712 or equivalent ARM64 / x86_64 CPU
- **Memory:** 4GB RAM minimum (8GB RAM recommended)
- **Storage:** 16GB MicroSDXC or higher
- **Display:** 1080p Full HD monitor via HDMI

---
## License

Distributed under the MIT License. See LICENSE for details.
