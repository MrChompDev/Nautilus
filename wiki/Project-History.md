# Project History

Timeline reconstructed from git history.

## v1 — the full suite (removed)

The original Nautilus OS grew a complete application suite: Abyssal IDE,
Surfline browser, Riptide audio, Cinema, Logbook notes, Mariner calculator,
Current telemetry, Harbor file manager, Tide terminal, Anchor settings, Reef
messenger, and the Kraken AI engine (CLI + GUI + training pipeline). The README
still documents much of this era, including its design language:

- Ocean palette: abyss-navy `#081626`, seafoam accent `#00F2C2`, HD-white text.
- Glassmorphism shell surfaces over a generated ocean wallpaper.
- Login dialog, app grid/Launchpad, global search, keyboard shortcuts
  (`Ctrl+Alt+<letter>` per app).
- Kraken shipped via `pyproject.toml` with agent specs and an error-learning
  SQLite memory under `~/.kraken/`.

## The restart — commit `c9cf26a`

> "Removed all the apps and restarting the project I have kept docs and AI
> training I am restarting the whole project from scratch"

Everything except docs/AI assets was deleted; development restarted from the
core upward.

## v2 — rebuild from the core up (current)

| Commit | What landed |
| :--- | :--- |
| `ccdaebc` | `core/theme.py` — new design system module |
| `337e5e0` | Shell main window + TopBar with live clock |
| `7a4625b` | Minor bug fixes |
| `97020de` | Central widget + vertical layout with TopBar |
| `ed0a52d` | Surfline browser app + dock integration |
| `bdb5866` *(HEAD)* | Surfline tab bar strip + themed home page |

## Design-language pivot

v2 swapped the ocean-dark theme for a warm **sand / wood / coral** palette
(see [Design System](Design-System.md)) while keeping the nautical naming and
the glass-surface idea (translucent sand bars instead of navy glass). The
README's "abyss navy" description predates this pivot — treat the wiki and
`core/theme.py` as source of truth for current visuals.

See [Roadmap](Roadmap.md) for what's next.
