# Anchor Settings

**The Nautilus control center** — display, network, audio, theme, and system
info in a single window.

- **Launch:** `python3 apps/anchor/main.py` or `Ctrl+Alt+,`
- **Memory target:** ~20 MB
- **UI:** PySide6 (single file, ~860 lines)

## Overview

Anchor is a five-tab settings panel: Display, Network, Audio, Theme, and
About. It reuses the Nautilus design tokens and applies theme changes live.

## Tabs

### Display
- Resolution, scaling, and refresh-rate controls.
- Appearance toggles.

### Network
- Wi-Fi network combos.
- Real Bluetooth scan (a `QThread` scanner; optional `bleak`, with a
  PowerShell fallback on Windows).
- Honest VPN/proxy status (it reports what it actually detects).
- Public IP check via `api.ipify.org` from a background thread.

### Audio
- Device selection, volume, balance, and gain sliders.
- SFX toggles.

### Theme
- Live `QColorDialog` overrides of the 10 Nautilus color tokens, with a
  reset-to-defaults button.

### About
- System info, including the memory base (**under 350 MB**) and version
  `v1.0.0 Build 2026.08.01`.

## Dependencies

| Package | Purpose |
| :--- | :--- |
| `bleak` (optional) | Bluetooth scanning (falls back to PowerShell) |
| stdlib `urllib` | Public IP check |
