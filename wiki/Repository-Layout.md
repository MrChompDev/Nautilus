# Repository Layout

What every folder and file in the repo is for.

```
Nautilus/
├── AGENTS.md               # Instructions for AI coding agents (brain map, commands)
├── README.md               # Public readme — still describes much of the v1 suite
├── LICENSE                 # MIT
├── requirements.txt        # All OS + app Python dependencies
├── pyproject.toml          # Kraken AI packaging (`pip install .`)
├── ruff.toml               # Lint configuration (see Testing & Linting)
│
├── core/
│   ├── main.py             # Desktop shell entry point (TopBar, Dock, NautilusShell)
│   └── theme.py            # Design tokens: COLORS, FONTS, RADIUS_*
│
├── apps/
│   ├── __init__.py
│   └── surfline/
│       └── app.py          # Surfline browser (Qt WebEngine)
│
├── agents/
│   └── DatabaseArchitect.md  # Example Kraken agent spec (YAML front-matter + MD)
│
├── models/                 # AI training assets (~196 MB, not imported by code)
│   ├── data/               # Corpora: kraken/, leviathan/, megalodon/, charybdis/,
│   │                       #   coding/, pentest/, writing/, download_datasets.py
│   ├── lm/ · imggen/ · trained/
│   └── __init__.py
│
├── wiki/                   # This wiki
├── docs/                   # Architecture docs & PRDs (empty after restart)
├── tests/                  # Smoke + unit tests (empty after restart)
├── data/                   # Runtime data (empty)
├── logs/                   # Runtime logs (empty)
└── .venv/                  # Local virtualenv (git-ignored)
```

## Dependency map (requirements.txt)

| Package | Consumer |
| :--- | :--- |
| `PySide6>=6.5.0` | Shell + all apps (UI framework) |
| `psutil>=5.9.0` | Current telemetry app (planned) |
| `cryptography>=42.0` | Surfline password vault AES-GCM (planned feature) |
| `requests>=2.31.0` | Riptide streaming APIs (planned) |
| `pygame>=2.5.0` | Riptide audio engine + SFX board (planned) |

Everything else in the codebase is pure stdlib.

Related pages: [Architecture](Architecture.md), [Roadmap](Roadmap.md),
[Kraken AI](Kraken-AI.md).
