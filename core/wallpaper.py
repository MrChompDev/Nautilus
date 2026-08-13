"""
Nautilus OS — Programmatic Desktop Wallpaper
Renders a fully custom deep-ocean themed wallpaper at the primary screen
resolution and caches it to assets/wallpaper.png.

Requires an active QGuiApplication (so QPixmap painting is safe).
"""

import math
import os
import random

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
WALLPAPER_PATH = os.path.join(ASSETS_DIR, "wallpaper.png")

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

ACCENT = (0, 242, 194)     # seafoam
ACCENT_DIM = (0, 201, 160) # seafoam_dim
STAR = (238, 244, 248)     # hd_white


def _draw_background(p: QPainter, w: int, h: int):
    grad = QLinearGradient(0, 0, 0, h)
    grad.setColorAt(0.00, QColor("#02060A"))
    grad.setColorAt(0.45, QColor("#050D14"))
    grad.setColorAt(0.80, QColor("#0A1E2E"))
    grad.setColorAt(1.00, QColor("#103244"))
    p.fillRect(0, 0, w, h, grad)

    glow = QRadialGradient(QPointF(w * 0.5, h * 0.36), h * 0.5)
    glow.setColorAt(0.0, QColor(*ACCENT, 20))
    glow.setColorAt(1.0, QColor(*ACCENT, 0))
    p.fillRect(0, 0, w, h, glow)

    glow2 = QRadialGradient(QPointF(w * 0.86, h * 0.18), h * 0.34)
    glow2.setColorAt(0.0, QColor(*ACCENT_DIM, 16))
    glow2.setColorAt(1.0, QColor(*ACCENT_DIM, 0))
    p.fillRect(0, 0, w, h, glow2)


def _draw_stars(p: QPainter, w: int, h: int):
    rng = random.Random(42)
    p.setPen(Qt.NoPen)
    for _ in range(160):
        x = rng.random() * w
        y = rng.random() * h * 0.78
        r = rng.random() * 1.6 + 0.4
        a = int(35 + rng.random() * 85)
        p.setBrush(QColor(*STAR, a))
        p.drawEllipse(QPointF(x, y), r, r)


def _draw_bubbles(p: QPainter, w: int, h: int):
    rng = random.Random(7)
    p.setPen(Qt.NoPen)
    for _ in range(30):
        x = rng.random() * w
        y = rng.random() * h
        rad = 2 + rng.random() * 11
        a = int(18 + rng.random() * 40)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(*ACCENT, a), 1))
        p.drawEllipse(QPointF(x, y), rad, rad)
    p.setPen(Qt.NoPen)


def _draw_depth_waves(p: QPainter, w: int, h: int):
    layers = [
        (0.72, 34, ACCENT, 12),
        (0.82, 52, ACCENT, 18),
        (0.92, 68, ACCENT_DIM, 24),
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
        p.fillPath(path, QColor(*color, alpha))


def _draw_wheel(p: QPainter, w: int, h: int):
    cx, cy = w * 0.16, h * 0.30
    R = min(w, h) * 0.11
    pen = QPen(QColor(*ACCENT, 38), 3)
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
    p.setBrush(QColor(*ACCENT, 26))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy), R * 0.22, R * 0.22)


def _draw_anchor(p: QPainter, w: int, h: int):
    cx, cy = w * 0.84, h * 0.72
    s = min(w, h) * 0.10
    pen = QPen(QColor(*ACCENT, 30), 3)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(cx, cy - s * 0.9), QPointF(cx, cy + s * 0.5))
    p.drawLine(QPointF(cx - s * 0.7, cy - s * 0.2), QPointF(cx + s * 0.7, cy - s * 0.2))
    p.drawArc(cx - s * 0.55, cy - s * 1.0, s * 1.1, s * 1.1, 0, 180 * 16)
    p.drawArc(cx - s * 0.65, cy - s * 0.4, s * 1.3, s * 0.6, 0, 180 * 16)
    p.drawLine(QPointF(cx - s * 0.55, cy - s * 0.2), QPointF(cx - s * 0.55, cy + s * 0.45))
    p.drawLine(QPointF(cx + s * 0.55, cy - s * 0.2), QPointF(cx + s * 0.55, cy + s * 0.45))


def generate_wallpaper(width: int = 1920, height: int = 1080, force: bool = False) -> str:
    """Generate (or reuse a matching cached) wallpaper PNG and return its path."""
    path = WALLPAPER_PATH
    if os.path.exists(path) and not force:
        probe = QPixmap(path)
        if not probe.isNull() and probe.width() == width and probe.height() == height:
            return path

    pm = QPixmap(width, height)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    _draw_background(p, width, height)
    _draw_stars(p, width, height)
    _draw_wheel(p, width, height)
    _draw_anchor(p, width, height)
    _draw_bubbles(p, width, height)
    _draw_depth_waves(p, width, height)

    p.end()

    os.makedirs(ASSETS_DIR, exist_ok=True)
    pm.save(path, "PNG")
    return path
