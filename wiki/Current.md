# Current Telemetry

**Real-time CPU, RAM, thermal, and process-tree monitoring** — the smallest
app in Nautilus.

- **Launch:** `python3 apps/Current/main.py` or `Ctrl+Alt+C`
- **Memory target:** ~15 MB
- **UI:** PySide6 (single file, ~600 lines)

## Overview

Current shows live system health with a set of metric cards and a color-coded
process tree. It polls once per second from a background thread, so the UI
never stutters.

## Features

- **SystemCollector** — a `QThread` that polls system metrics every second via
  `psutil`: per-core and total CPU %, frequency, RAM, swap, disk, sensor
  temperatures, battery, network I/O deltas, and uptime. Falls back to a
  zero-metrics mode if `psutil` is absent.
- **MetricCards** — label + value + a 3 px progress bar per metric.
- **Process tree** — top-100 processes by RSS with color coding
  (coral > 500 MB, amber > 200 MB).
- **Kill processes** — SIGKILL / `taskkill` with a confirmation dialog.

## Dependencies

| Package | Purpose |
| :--- | :--- |
| `psutil` | System metrics collection |
