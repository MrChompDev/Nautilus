# Nautilus OS Wiki

**Nautilus OS** is a lightweight desktop environment for the **Raspberry Pi 500**, built
entirely in Python on [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python).
It uses a nautical naming scheme throughout — the shell is the *ship*, apps are
named after ocean phenomena (*Surfline*, *Abyssal*, *Kraken*…), and the design
system lives in a single *theme* module.

> **Current status:** The project was **restarted from scratch** (commit `c9cf26a`).
> Today the codebase contains the desktop shell (`core/main.py`), the shared design
> system (`core/theme.py`), and one app (**Surfline** browser). The README still
> describes the larger v1 application suite — see [Roadmap](Roadmap.md) for what's
> implemented vs. planned.

## Quick facts

| | |
| :--- | :--- |
| Language | Python 3.11+ (target `py313`) |
| UI framework | PySide6 ≥ 6.5 (Qt 6) |
| Primary target | Raspberry Pi 500 (ARM64), also Linux/Windows x64 |
| Entry point | `python3 core/main.py` |
| License | MIT |

## Pages

- **[Getting Started](Getting-Started.md)** — requirements, installation, running.
- **[Architecture](Architecture.md)** — how the system fits together.
- **[The Shell](Shell.md)** — `core/main.py`: TopBar, Dock, NautilusShell.
- **[Design System](Design-System.md)** — theme tokens and styling conventions.
- **[Surfline Browser](Surfline.md)** — the first app, built on Qt WebEngine.
- **[Roadmap](Roadmap.md)** — full milestone plan: M0 shell foundation through
  M6 release, every app with its feature set.
- **[Master TODO](../TODO.md)** — flat checkable task list for all apps.
- **[Kraken AI](Kraken-AI.md)** — packaging, CLI entry points, agent specs.
- **[Testing & Linting](Testing-and-Linting.md)** — ruff config, test strategy.
- **[Repository Layout](Repository-Layout.md)** — every folder explained.
- **[Project History](Project-History.md)** — v1 → v2 timeline from git history.
- **[Glossary](Glossary.md)** — the nautical naming scheme decoded.
