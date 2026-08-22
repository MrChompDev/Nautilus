# Design System

The entire visual language of Nautilus OS is defined in one file:
[`core/theme.py`](../core/theme.py). Every widget stylesheet is an f-string over
these tokens — **never hardcode a color, font, or radius in app code**.

## `COLORS`

The current (v2) palette is warm sand + wood + coral — deliberately different
from the v1 "abyss navy" ocean theme described in the README.

### Backgrounds

| Token | Hex | Usage |
| :--- | :--- | :--- |
| `bg_light` | `#E8DCC8` | Main window backdrops |
| `bg_mid` | `#D4C8B0` | Toolbars, nav bars, dock buttons |
| `bg_dark` | `#C2B49A` | Sidebars, tab strips, pressed panels |

### Wood tones

| Token | Hex |
| :--- | :--- |
| `wood` | `#8B6F47` |
| `wood_light` | `#A68B5B` |
| `wood_dark` | `#6B5535` |

### Accent

| Token | Hex | Usage |
| :--- | :--- | :--- |
| `coral` | `#FF6F61` | Primary accent — focus borders, links |
| `coral_dim` | `#FF8E80` | Hover variants |
| `coral_deep` | `#E55B50` | Active/pressed variants |

### Text

| Token | Hex | Usage |
| :--- | :--- | :--- |
| `text` | `#2C2C2C` | Body text |
| `text_dark` | `#1A1A1A` | Headings, primary text |
| `text_muted` | `#4D4D4D` | Secondary/hint text |

### Status / surfaces / borders

| Token group | Values |
| :--- | :--- |
| Status | `success #4CAF50`, `warning #FFC107`, `error #F44336` |
| Surfaces | `hover #F5F5F5`, `pressed #E0E0E0`, `selected #D1C4E9` |
| Borders | `border #BDBDBD`, `border_light #E0E0E0`, `border_dark #9E9E9E` |

## `FONTS`

| Key | Value |
| :--- | :--- |
| `ui` | Segoe UI |
| `mono` | JetBrains Mono |
| sizes | `size_xs 10` · `size_sm 12` · `size_md 14` · `size_lg 16` · `size_xl 18` · `size_xxl 20` · `size_title 24` |

## Radius tokens

Plain strings ready for QSS interpolation:

```python
RADIUS_SM = "8px"
RADIUS_MD = "12px"
RADIUS_LG = "16px"
```

## Styling conventions

1. Import only what you use: `from core.theme import COLORS, FONTS, RADIUS_MD`.
2. Build QSS with f-strings; scope rules to the widget class
   (`QFrame {{ ... }}`) so setStyleSheet stays local.
3. Interactive widgets define all three states: normal, `:hover`, `:pressed`.
4. Text inputs get a coral focus border (`QLineEdit:focus`).
5. Monospace (`FONTS['mono']`) is used for anything technical — clocks, URLs,
   wordmarks; UI font for prose and titles.
