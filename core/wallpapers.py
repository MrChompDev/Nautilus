"""Nautilus OS — Wallpaper System.

Theme catalog + persisted selection + programmatic/AI resolution and the
ambient animation layer that makes a wallpaper feel alive.

Config lives in ~/.nautilus/wallpaper.json:
    {"theme": "abyss", "animated": true}

Resolution order for a theme (same convention as icons.py / ai_assets.py):
    1. assets/wallpapers/<theme>.png on disk  (AI-generated or programmatic)
    2. programmatic variant generated on demand into that path

core.ai_assets.py is the AI driver that overwrites the same output paths;
this module never imports it, so there is no circular dependency.
"""

import json
import math
import os
import random

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
WALLPAPERS_DIR = os.path.join(ASSETS_DIR, "wallpapers")

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".nautilus")
CONFIG_PATH = os.path.join(CONFIG_DIR, "wallpaper.json")

DEFAULT_THEME = "abyss"
DEFAULT_ANIMATED = True

# ═══════════════════════════════════════════════════════════════
#  THEME CATALOG
# ═══════════════════════════════════════════════════════════════

THEMES: dict[str, dict] = {
    "abyss": {
        "name": "Abyssal Deep",
        "description": "Near-black abyss with bioluminescent seafoam light streaks.",
        "animated": True,
        "prompt": (
            "Ultra-wide deep ocean desktop wallpaper, abyssal theme, dark navy gradient "
            "from near-black at the top to deep teal at the bottom, glowing bioluminescent "
            "seafoam light streaks, faint stars above a calm sea, subtle depth waves, "
            "minimalist elegant composition, dark and moody, high detail, 16:9"
        ),
    },
    "aurora": {
        "name": "Polar Aurora",
        "description": "Seafoam and teal aurora ribbons over a still night ocean.",
        "animated": True,
        "prompt": (
            "Ultra-wide polar night ocean desktop wallpaper, aurora borealis glowing in "
            "seafoam teal and soft green over a calm dark sea, subtle stars, faint reflection "
            "of the aurora on the water, minimalist elegant, dark and moody, high detail, 16:9"
        ),
    },
    "tide": {
        "name": "Coral Tide",
        "description": "Warm coral and amber shallow reef with drifting bubbles.",
        "animated": True,
        "prompt": (
            "Ultra-wide underwater desktop wallpaper, warm coral reef scene at dusk, soft amber "
            "and coral bioluminescent glow, gentle bubbles rising, deep teal water gradient, "
            "minimalist elegant composition, calm and moody, high detail, 16:9"
        ),
    },
    "storm": {
        "name": "Midnight Storm",
        "description": "Deep slate swell under a stormy sky with a faint lightning bolt.",
        "animated": True,
        "prompt": (
            "Ultra-wide midnight storm ocean desktop wallpaper, churning deep slate waves, dark "
            "storm clouds, a single faint fork of lightning, cold moody atmosphere, high contrast "
            "minimalist composition, dark and cinematic, high detail, 16:9"
        ),
    },
    "kelp": {
        "name": "Kelp Forest",
        "description": "Towering emerald kelp strands glowing with seafoam light.",
        "animated": True,
        "prompt": (
            "Ultra-wide underwater desktop wallpaper, towering kelp forest rising from the dark, "
            "emerald green strands glowing with seafoam bioluminescence, rays of light from above, "
            "fine bubbles, minimalist elegant, dark and moody, high detail, 16:9"
        ),
    },
    "stars": {
        "name": "Sea of Stars",
        "description": "Star-dense night sky mirrored in a glassy calm ocean.",
        "animated": False,
        "prompt": (
            "Ultra-wide night ocean desktop wallpaper, dense field of stars over a perfectly calm "
            "glassy sea, stars faintly mirrored on the water, deep indigo and navy gradient, "
            "minimalist elegant composition, serene and moody, high detail, 16:9"
        ),
    },
}


def list_themes() -> list[dict]:
    """Ordered theme list with id + name + description + animated flag."""
    return [{"id": tid, **info} for tid, info in THEMES.items()]


def theme_info(theme_id: str) -> dict | None:
    return THEMES.get(theme_id)


def theme_accent(theme_id: str) -> tuple[int, int, int]:
    """RGB accent used by the ambient animation layer per theme."""
    accents = {
        "abyss": (0, 242, 194),
        "aurora": (64, 255, 180),
        "tide": (255, 138, 88),
        "storm": (170, 200, 255),
        "kelp": (0, 242, 194),
        "stars": (150, 180, 255),
    }
    return accents.get(theme_id, (0, 242, 194))


def wallpaper_path(theme_id: str) -> str:
    return os.path.join(WALLPAPERS_DIR, f"{theme_id}.png")


# ═══════════════════════════════════════════════════════════════
#  CONFIG (~/.nautilus/wallpaper.json)
# ═══════════════════════════════════════════════════════════════

def load_settings() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {"theme": DEFAULT_THEME, "animated": DEFAULT_ANIMATED}
    theme = data.get("theme", DEFAULT_THEME)
    if theme not in THEMES:
        theme = DEFAULT_THEME
    return {
        "theme": theme,
        "animated": bool(data.get("animated", THEMES[theme].get("animated", True))),
    }


def save_settings(theme: str | None = None, animated: bool | None = None) -> dict:
    current = load_settings()
    if theme is not None and theme in THEMES:
        current["theme"] = theme
    if animated is not None:
        current["animated"] = bool(animated)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(current, fh, indent=2)
    os.replace(tmp, CONFIG_PATH)
    return current


def get_theme() -> str:
    return load_settings()["theme"]


def get_animated() -> bool:
    return load_settings()["animated"]


def set_theme(theme_id: str) -> dict:
    return save_settings(theme=theme_id)


def set_animated(enabled: bool) -> dict:
    return save_settings(animated=enabled)


# ═══════════════════════════════════════════════════════════════
#  RESOLUTION
# ═══════════════════════════════════════════════════════════════

def _valid_png(path: str) -> bool:
    """Cheap sanity check: non-empty PNG with the PNG magic bytes."""
    try:
        if not os.path.exists(path) or os.path.getsize(path) < 64:
            return False
        with open(path, "rb") as fh:
            return fh.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def resolve_wallpaper(theme_id: str, width: int = 1920, height: int = 1080,
                      force: bool = False) -> str:
    """Return a ready-to-draw wallpaper path for the theme.

    Reuses any cached PNG (AI or programmatic) at any resolution — the shell
    scales it to the widget, exactly like the previous single-wallpaper flow.
    """
    if theme_id not in THEMES:
        theme_id = DEFAULT_THEME
    path = wallpaper_path(theme_id)
    if _valid_png(path) and not force:
        return path
    if theme_id == DEFAULT_THEME and not force:
        legacy = os.path.join(ASSETS_DIR, "wallpaper.png")
        if _valid_png(legacy):
            os.makedirs(WALLPAPERS_DIR, exist_ok=True)
            try:
                import shutil
                shutil.copy(legacy, path)
                return path
            except OSError:
                pass
    from core.wallpaper import generate_variant
    return generate_variant(theme_id, width, height, force=force)


# ═══════════════════════════════════════════════════════════════
#  AMBIENT ANIMATION LAYER
#  Drifting bioluminescent motes + a soft shimmer band painted over
#  the static base image. Cheap (seeded, ~40 particles, no blur), so it
#  runs comfortably on a Raspberry Pi-class CPU at 25fps.
# ═══════════════════════════════════════════════════════════════

class AmbientLayer:
    def __init__(self, width: int, height: int, seed: int = 2026,
                 density: int = 44, accent=(0, 242, 194)):
        self._w = max(width, 16)
        self._h = max(height, 16)
        self._t = 0.0
        self._rng = random.Random(seed)
        self._accent = accent
        self._motes = [self._new_mote() for _ in range(density)]

    def _new_mote(self) -> dict:
        return {
            "x": self._rng.random() * self._w,
            "y": self._rng.random() * self._h,
            "r": 0.6 + self._rng.random() * 2.4,
            "rise": 5.0 + self._rng.random() * 16.0,   # px/s upward drift
            "sway": 0.15 + self._rng.random() * 0.8,   # rad/s lateral sway
            "phase": self._rng.random() * 6.283,
            "alpha": 16 + self._rng.random() * 70,
        }

    def advance(self, dt: float):
        self._t += dt
        for m in self._motes:
            m["y"] -= m["rise"] * dt
            m["x"] += math.sin(self._t * m["sway"] + m["phase"]) * 10 * dt
            if m["y"] < -8:
                m["y"] = self._h + 8
                m["x"] = self._rng.random() * self._w
            if m["x"] < -8:
                m["x"] = self._w + 8
            elif m["x"] > self._w + 8:
                m["x"] = -8

    def draw(self, painter):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        acr, acg, acb = self._accent
        painter.setPen(Qt.NoPen)
        for m in self._motes:
            flicker = 0.55 + 0.45 * math.sin(self._t * 1.6 + m["phase"])
            alpha = int(m["alpha"] * flicker)
            painter.setBrush(QColor(acr, acg, acb, max(alpha, 4)))
            painter.drawEllipse(
                int(m["x"]), int(m["y"]), int(m["r"] * 2), int(m["r"] * 2)
            )

        # Soft horizontal shimmer band sweeping slowly upward near the base.
        y0 = self._h * (0.82 - 0.06 * math.sin(self._t * 0.2))
        painter.setBrush(QColor(acr, acg, acb, 10))
        painter.drawRect(0, int(y0), self._w, 2)
        painter.setBrush(QColor(acr, acg, acb, 6))
        painter.drawRect(0, int(y0 + 14), self._w, 2)


def ambient_layer(width: int, height: int, accent=(0, 242, 194)) -> AmbientLayer:
    return AmbientLayer(width, height, accent=accent)
