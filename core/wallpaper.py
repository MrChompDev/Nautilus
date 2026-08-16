"""
Nautilus OS — Programmatic Desktop Wallpaper
Renders the deep-ocean themed wallpapers at the primary screen resolution and
caches them to assets/wallpapers/<theme>.png.

The default "abyss" theme also keeps the legacy assets/wallpaper.png path so
older callers keep working. Requires an active QGuiApplication.

core/ai_assets.py can overwrite these same output paths with AI renders; the
shell picks whichever PNG is on disk (see core/wallpapers.py).
"""

import math
import os
import random

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
WALLPAPER_PATH = os.path.join(ASSETS_DIR, "wallpaper.png")
WALLPAPERS_DIR = os.path.join(ASSETS_DIR, "wallpapers")

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)

# Legacy accent constants (kept for backwards compatibility).
ACCENT = (0, 242, 194)     # seafoam
ACCENT_DIM = (0, 201, 160) # seafoam_dim
STAR = (238, 244, 248)     # hd_white

# ═══════════════════════════════════════════════════════════════
#  THEME PALETTES (gradient stops + accents + composition seeds)
# ═══════════════════════════════════════════════════════════════

PALETTES = {
    "abyss": {
        "top": "#02060A", "mid": "#050D14", "deep": "#0A1E2E", "base": "#103244",
        "accent": (0, 242, 194), "accent_dim": (0, 201, 160), "star": (238, 244, 248),
        "seed": 42, "stars": 160, "bubbles": 30,
    },
    "aurora": {
        "top": "#02060C", "mid": "#041018", "deep": "#0A1E2E", "base": "#12364E",
        "accent": (64, 255, 180), "accent_dim": (40, 210, 255), "star": (220, 240, 255),
        "seed": 13, "stars": 200, "bubbles": 0,
    },
    "tide": {
        "top": "#071018", "mid": "#0A1C24", "deep": "#1B3A44", "base": "#2A4A50",
        "accent": (255, 138, 88), "accent_dim": (255, 176, 110), "star": (255, 244, 230),
        "seed": 7, "stars": 0, "bubbles": 44,
    },
    "storm": {
        "top": "#030507", "mid": "#060A10", "deep": "#0C121C", "base": "#16222E",
        "accent": (170, 200, 255), "accent_dim": (120, 150, 210), "star": (200, 210, 235),
        "seed": 99, "stars": 0, "bubbles": 0,
    },
    "kelp": {
        "top": "#04120E", "mid": "#07221A", "deep": "#0E3A2C", "base": "#16543E",
        "accent": (0, 242, 194), "accent_dim": (40, 200, 140), "star": (210, 250, 235),
        "seed": 3, "stars": 40, "bubbles": 26,
    },
    "stars": {
        "top": "#030614", "mid": "#060B24", "deep": "#0C1236", "base": "#141B44",
        "accent": (150, 180, 255), "accent_dim": (110, 140, 230), "star": (235, 240, 255),
        "seed": 21, "stars": 420, "bubbles": 0,
    },
}


def _palette(theme_id: str) -> dict:
    return PALETTES.get(theme_id, PALETTES["abyss"])


# ═══════════════════════════════════════════════════════════════
#  COMPOSITION PRIMITIVES
# ═══════════════════════════════════════════════════════════════

def _draw_background(p: QPainter, w: int, h: int, pal: dict):
    grad = QLinearGradient(0, 0, 0, h)
    grad.setColorAt(0.00, QColor(pal["top"]))
    grad.setColorAt(0.45, QColor(pal["mid"]))
    grad.setColorAt(0.80, QColor(pal["deep"]))
    grad.setColorAt(1.00, QColor(pal["base"]))
    p.fillRect(0, 0, w, h, grad)

    accent, accent_dim = pal["accent"], pal["accent_dim"]
    glow = QRadialGradient(QPointF(w * 0.5, h * 0.36), h * 0.5)
    glow.setColorAt(0.0, QColor(*accent, 20))
    glow.setColorAt(1.0, QColor(*accent, 0))
    p.fillRect(0, 0, w, h, glow)

    glow2 = QRadialGradient(QPointF(w * 0.86, h * 0.18), h * 0.34)
    glow2.setColorAt(0.0, QColor(*accent_dim, 16))
    glow2.setColorAt(1.0, QColor(*accent_dim, 0))
    p.fillRect(0, 0, w, h, glow2)


def _draw_stars(p: QPainter, w: int, h: int, pal: dict, count: int = 160):
    rng = random.Random(pal["seed"])
    star = pal["star"]
    p.setPen(Qt.NoPen)
    for _ in range(count):
        x = rng.random() * w
        y = rng.random() * h * 0.82
        r = rng.random() * 1.6 + 0.4
        a = int(35 + rng.random() * 85)
        p.setBrush(QColor(*star, a))
        p.drawEllipse(QPointF(x, y), r, r)


def _draw_bubbles(p: QPainter, w: int, h: int, pal: dict, count: int = 30):
    rng = random.Random((pal["seed"] * 7) % 97)
    accent = pal["accent"]
    p.setPen(Qt.NoPen)
    for _ in range(count):
        x = rng.random() * w
        y = rng.random() * h
        rad = 2 + rng.random() * 11
        a = int(18 + rng.random() * 40)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(*accent, a), 1))
        p.drawEllipse(QPointF(x, y), rad, rad)
    p.setPen(Qt.NoPen)


def _draw_depth_waves(p: QPainter, w: int, h: int, pal: dict,
                      layers=None, alpha_scale: int = 1):
    accent, accent_dim = pal["accent"], pal["accent_dim"]
    layers = layers or [
        (0.72, 34, accent, 12),
        (0.82, 52, accent, 18),
        (0.92, 68, accent_dim, 24),
    ]
    for idx, (base, amp, color, alpha) in enumerate(layers):
        path = QPainterPath()
        path.moveTo(0, h)
        path.lineTo(0, base * h)
        for x in range(0, w + 1, 8):
            y = (base * h
                 + amp * math.sin(x * 0.0052 * (idx + 1) + idx * 1.3)
                 + 16 * math.cos(x * 0.0017 + idx))
            path.lineTo(x, y)
        path.lineTo(w, h)
        path.closeSubpath()
        p.fillPath(path, QColor(*color, alpha * alpha_scale))


def _draw_wheel(p: QPainter, w: int, h: int, pal: dict):
    accent = pal["accent"]
    cx, cy = w * 0.16, h * 0.30
    R = min(w, h) * 0.11
    pen = QPen(QColor(*accent, 38), 3)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(cx, cy), R, R)
    for i in range(8):
        ang = i * math.pi / 4
        x1 = cx + R * 0.35 * math.cos(ang)
        y1 = cy + R * 0.35 * math.sin(ang)
        x2 = cx + R * 0.95 * math.cos(ang)
        y2 = cy + R * 0.95 * math.sin(ang)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    p.setBrush(QColor(*accent, 26))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy), R * 0.22, R * 0.22)


def _draw_anchor(p: QPainter, w: int, h: int, pal: dict):
    accent = pal["accent"]
    cx, cy = w * 0.84, h * 0.72
    s = min(w, h) * 0.10
    pen = QPen(QColor(*accent, 30), 3)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(cx, cy - s * 0.9), QPointF(cx, cy + s * 0.5))
    p.drawLine(QPointF(cx - s * 0.7, cy - s * 0.2), QPointF(cx + s * 0.7, cy - s * 0.2))
    p.drawArc(cx - s * 0.55, cy - s * 1.0, s * 1.1, s * 1.1, 0, 180 * 16)
    p.drawArc(cx - s * 0.65, cy - s * 0.4, s * 1.3, s * 0.6, 0, 180 * 16)
    p.drawLine(QPointF(cx - s * 0.55, cy - s * 0.2), QPointF(cx - s * 0.55, cy + s * 0.45))
    p.drawLine(QPointF(cx + s * 0.55, cy - s * 0.2), QPointF(cx + s * 0.55, cy + s * 0.45))


def _draw_aurora(p: QPainter, w: int, h: int, pal: dict):
    rng = random.Random(pal["seed"] + 5)
    accent, accent_dim = pal["accent"], pal["accent_dim"]
    p.setPen(Qt.NoPen)
    for band in range(4):
        base_y = h * (0.10 + 0.14 * band) + rng.random() * h * 0.04
        amp = h * (0.05 + 0.03 * rng.random())
        path = QPainterPath()
        path.moveTo(0, base_y)
        phase = rng.random() * 6.28
        for x in range(0, w + 1, 6):
            y = (base_y
                 + amp * math.sin(x * 0.006 + phase)
                 + amp * 0.5 * math.sin(x * 0.0023 - phase))
            path.lineTo(x, y)
        path.lineTo(w, base_y + h * 0.03)
        path.lineTo(0, base_y + h * 0.03)
        path.closeSubpath()
        color = accent if band % 2 == 0 else accent_dim
        p.setBrush(QColor(*color, 18 + band * 4))
        p.fillPath(path, p.brush())
    # Faint reflection of the bands on the water.
    reflect_y = int(h * 0.86)
    p.setBrush(QColor(*accent, 8))
    p.fillRect(0, reflect_y, w, int(h * 0.06), p.brush())


def _draw_lightning(p: QPainter, w: int, h: int, pal: dict):
    rng = random.Random(pal["seed"] + 3)
    x = w * (0.5 + 0.25 * rng.random())
    top = h * 0.06
    bot = h * 0.55
    pts = [(x, top)]
    cur_x, cur_y = x, top
    segs = 7
    for i in range(segs):
        cur_x += rng.uniform(-0.05, 0.05) * w
        cur_y += (bot - top) / segs * (0.9 + 0.25 * rng.random())
        pts.append((cur_x, cur_y))
    pts.append((x - w * 0.012, bot))
    pen = QPen(QColor(*pal["accent"], 70), max(2, int(min(w, h) * 0.002)))
    p.setPen(pen)
    for i in range(len(pts) - 1):
        p.drawLine(QPointF(*pts[i]), QPointF(*pts[i + 1]))


def _draw_kelp(p: QPainter, w: int, h: int, pal: dict):
    rng = random.Random(pal["seed"] + 9)
    accent, accent_dim = pal["accent"], pal["accent_dim"]
    p.setPen(Qt.NoPen)
    n = max(6, int(w / 90))
    for i in range(n):
        x = w * (0.05 + 0.9 * i / max(n - 1, 1)) + rng.uniform(-w * 0.02, w * 0.02)
        height = h * (0.55 + 0.35 * rng.random())
        width = min(w, h) * (0.010 + 0.008 * rng.random())
        sway = rng.random() * 6.28
        path = QPainterPath()
        path.moveTo(x - width, h)
        for y in range(h, int(h - height), -8):
            dx = width * 0.8 * math.sin(y * 0.01 + sway)
            path.lineTo(x + dx, y)
        path.lineTo(x + width, h)
        path.closeSubpath()
        color = accent if i % 3 else accent_dim
        p.setBrush(QColor(*color, 22 + (i % 4) * 6))
        p.fillPath(path, p.brush())
    # Light shafts from the surface.
    light = QRadialGradient(QPointF(w * 0.5, h * 0.05), h * 0.5)
    light.setColorAt(0.0, QColor(*accent, 14))
    light.setColorAt(1.0, QColor(*accent, 0))
    p.fillRect(0, 0, w, h, light)


# ═══════════════════════════════════════════════════════════════
#  THEME COMPOSITORS
# ═══════════════════════════════════════════════════════════════

def _compose(theme_id: str, p: QPainter, w: int, h: int, pal: dict):
    _draw_background(p, w, h, pal)

    if theme_id == "abyss":
        _draw_stars(p, w, h, pal, pal["stars"])
        _draw_wheel(p, w, h, pal)
        _draw_anchor(p, w, h, pal)
        _draw_bubbles(p, w, h, pal, pal["bubbles"])
        _draw_depth_waves(p, w, h, pal)
    elif theme_id == "aurora":
        _draw_stars(p, w, h, pal, pal["stars"])
        _draw_aurora(p, w, h, pal)
        _draw_depth_waves(p, w, h, pal, alpha_scale=2)
    elif theme_id == "tide":
        _draw_bubbles(p, w, h, pal, pal["bubbles"])
        _draw_depth_waves(p, w, h, pal, alpha_scale=2)
    elif theme_id == "storm":
        _draw_lightning(p, w, h, pal)
        layers = [
            (0.70, 60, pal["accent_dim"], 10),
            (0.80, 82, pal["accent_dim"], 14),
            (0.90, 96, pal["accent"], 18),
        ]
        _draw_depth_waves(p, w, h, pal, layers=layers)
    elif theme_id == "kelp":
        _draw_stars(p, w, h, pal, pal["stars"])
        _draw_kelp(p, w, h, pal)
        _draw_bubbles(p, w, h, pal, pal["bubbles"])
        _draw_depth_waves(p, w, h, pal, alpha_scale=2)
    else:  # stars
        _draw_stars(p, w, h, pal, pal["stars"])
        # Mirror the starfield in the glassy ocean.
        mirror = QLinearGradient(0, h * 0.72, 0, h)
        mirror.setColorAt(0.0, QColor(*pal["star"], 0))
        mirror.setColorAt(1.0, QColor(*pal["star"], 22))
        p.fillRect(0, int(h * 0.72), w, int(h * 0.28), mirror)
        _draw_depth_waves(p, w, h, pal, layers=[
            (0.74, 20, pal["accent_dim"], 8),
            (0.90, 30, pal["accent"], 10),
        ])


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════

def _render(theme_id: str, width: int, height: int) -> str:
    pal = _palette(theme_id)
    pm = QPixmap(width, height)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _compose(theme_id, p, width, height, pal)
    p.end()

    os.makedirs(WALLPAPERS_DIR, exist_ok=True)
    path = os.path.join(WALLPAPERS_DIR, f"{theme_id}.png")
    pm.save(path, "PNG")
    return path


def generate_variant(theme_id: str, width: int = 1920, height: int = 1080,
                     force: bool = False) -> str:
    """Generate (or reuse a matching cached) PNG for a theme."""
    if theme_id not in PALETTES:
        theme_id = "abyss"
    path = os.path.join(WALLPAPERS_DIR, f"{theme_id}.png")
    if os.path.exists(path) and not force:
        probe = QPixmap(path)
        if not probe.isNull() and probe.width() == width and probe.height() == height:
            return path
    return _render(theme_id, width, height)


def generate_wallpaper(width: int = 1920, height: int = 1080, force: bool = False) -> str:
    """Legacy entry point: renders the default "abyss" theme to
    assets/wallpaper.png (the historical single-path behaviour)."""
    path = WALLPAPER_PATH
    if os.path.exists(path) and not force:
        probe = QPixmap(path)
        if not probe.isNull() and probe.width() == width and probe.height() == height:
            return path

    pm = QPixmap(width, height)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _compose("abyss", p, width, height, _palette("abyss"))
    p.end()

    os.makedirs(ASSETS_DIR, exist_ok=True)
    pm.save(path, "PNG")
    return path
