# Testing & Linting

> **Restart note:** `tests/` is currently empty — the v1 test suite was removed
> with the rest of the apps. This page documents the tooling conventions that
> are in place (lint config) and the testing approach v1 used, which v2 will
> rebuild on.

## Linting — ruff

Config lives in [`ruff.toml`](../ruff.toml):

- **Line length:** 120 · **Target:** `py313`
- **Excluded paths:** `pipcache`, `assets`, `tests`, `.git`, `data`,
  `apps/Surfline/assets`
- **Rule set** (`select`): real bugs (`F`), syntax errors (`E9`), basic style
  (`E4`/`E7`), import hygiene (`I`), modernization (`UP`), bugbear (`B`),
  comprehensions (`C`), performance hints (`PERF`) — intentionally narrower
  than ruff's default to keep signal high.

Notable deliberate ignores:

| Code | Why |
| :--- | :--- |
| `E402` | Imports after `sys.path` setup — required for standalone app launches |
| `BLE001`, `S110` | Defensive bare excepts / try-pass are accepted in UI event handlers |
| `DTZ005/006` | Naive local datetimes are fine for a desktop app |
| `C901` | Complexity flagged as refactor hint, not error |
| `N999` | Scratch/test module naming freedom |

Run it:

```sh
python3 -m ruff check .
```

## Test strategy (v1 pattern, to be restored)

- **Smoke test** — launched every app standalone for ~4 s each and reported
  failures; supported single-app runs. The modern equivalent would live at
  `tests/smoke_test.py`.
- **Engine unit tests** — Kraken had dedicated suites
  (`test_kraken_engine.py`, `test_kraken_agents.py`,
  `test_kraken_providers.py`) run as plain scripts.

## Headless / CI environment

Qt and SDL need dummy drivers when no display exists:

```sh
export QT_QPA_PLATFORM=offscreen
export SDL_AUDIODRIVER=dummy SDL_VIDEODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1
export QTWEBENGINE_DISABLE_SANDBOX=1
```

## Manual verification today

With no automated tests yet, verify changes by running the shell and exercising
the UI:

```sh
python3 core/main.py     # shell boots; clock ticks; dock opens Surfline
```

then lint: `python3 -m ruff check .`
