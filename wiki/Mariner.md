# Mariner

**A scientific calculator with an expression parser, history tape, and
navigation helpers.**

- **Launch:** `python3 apps/Mariner/main.py` or `Ctrl+Alt+E`
- **Memory target:** ~20 MB
- **UI:** PySide6 (single file, ~610 lines)

## Overview

Mariner is Nautilus' tiny-but-capable calculator. It evaluates full
expressions through a hand-written recursive-descent parser — no `eval()`, no
external math engine beyond the stdlib.

## Features

- **ExpressionEvaluator** — a hand-written tokenizer + recursive-descent
  parser (`expr/term/factor/power/atom`) over a whitelisted math vocabulary:
  `sin`, `cos`, `tan`, `log`, `ln`, `exp`, `sqrt`, `fact`, `gcd`, plus the
  constants `pi`, `e`, `tau`, and `phi`.
- **Full operator support** — unary minus, `^` power, `!` factorial (gamma
  fallback), `%`, and parentheses.
- **Live result preview** — the result updates as you type.
- **History tape** — previous results persist to `history.json` (capped at
  200 entries) and are recalled with a click.
- **Robust output** — handles scientific notation, `INF`, and `NaN` gracefully.

## Example Expressions

```
sqrt(2) ^ 10
sin(pi / 6) + cos(tau / 4)
fact(7)
gcd(84, 36)
```

## Implementation Notes

The parser lives entirely inside `apps/Mariner/main.py` and uses only the
Python standard library, keeping the app to ~20 MB of RAM.
