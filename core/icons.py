"""
Nautilus OS — App Icon & Logo Generator
Programmatically generates SVG logo icons for all Nautilus applications.

Each app gets a themed 128x128 programmatic QPixmap icon.
Icons are cached to assets/logos/ on first generation.
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGOS_DIR = os.path.join(PROJECT_ROOT, "assets", "logos")

from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap

try:
    from core.theme import COLORS
except ImportError:
    COLORS = {"seafoam": "#00F2C2", "abyss_navy": "#081626", "void_black": "#02060A",
              "slate_navy": "#0E2238", "deep_navy": "#050D14", "coral": "#FF7F50",
              "amber": "#FFA502", "hd_white": "#EEF4F8"}


def _logo_path(app_id: str) -> str:
    os.makedirs(LOGOS_DIR, exist_ok=True)
    return os.path.join(LOGOS_DIR, f"{app_id}.png")


# ═══════════════════════════════════════════════════════════════
#  LOGO GENERATORS (each returns a QPixmap)
# ═══════════════════════════════════════════════════════════════

def _draw_base(p: QPainter, w: int, h: int, bg: str):
    p.fillRect(0, 0, w, h, QColor(bg))


def _draw_abyssal() -> QPixmap:
    """Abyssal IDE — deep ocean with code brackets."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    # Code brackets
    p.setPen(QPen(QColor(COLORS["seafoam"]), 6))
    font = QFont("JetBrains Mono", 40, QFont.Bold)
    p.setFont(font)
    p.drawText(QRect(0, 0, 50, 128), Qt.AlignCenter, "{")
    p.drawText(QRect(78, 0, 50, 128), Qt.AlignCenter, "}")

    # Slash
    p.setPen(QPen(QColor(COLORS["coral"]), 4))
    p.drawLine(70, 30, 58, 98)

    p.end()
    return pm


def _draw_surfline() -> QPixmap:
    """Surfline Browser — ocean wave."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["abyss_navy"])

    # Waves
    pen = QPen(QColor(COLORS["seafoam"]), 4)
    p.setPen(pen)
    for y_off in [70, 80, 90]:
        for x in range(0, 128, 2):
            y = y_off + int(8 * (__import__("math").sin(x * 0.1)))
            p.drawPoint(x, y)

    # Better wave with QPainterPath
    from PySide6.QtGui import QPainterPath
    wave = QPainterPath()
    wave.moveTo(0, 90)
    for x in range(129):
        wave.lineTo(x, 85 + 12 * __import__("math").sin(x * 0.08))
    wave.lineTo(128, 128)
    wave.lineTo(0, 128)
    wave.closeSubpath()
    p.fillPath(wave, QColor(COLORS["seafoam_deep"]))
    p.drawPath(wave)

    p.end()
    return pm


def _draw_riptide() -> QPixmap:
    """Riptide Audio — audio waveform."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["slate_navy"])

    # Audio bars
    bars = [40, 70, 55, 90, 60, 100, 50, 80, 65, 85, 45, 75]
    bar_w = 6
    gap = 4
    start_x = (128 - len(bars) * (bar_w + gap)) // 2
    center_y = 64

    for i, h in enumerate(bars):
        x = start_x + i * (bar_w + gap)
        color = QColor(COLORS["seafoam"]) if i % 3 != 0 else QColor(COLORS["amber"])
        p.fillRect(x, center_y - h // 2, bar_w, h, color)

    p.end()
    return pm


def _draw_current() -> QPixmap:
    """Current Telemetry — pulse graph."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    # Grid lines
    grid_pen = QPen(QColor(COLORS["slate_navy"]), 1, Qt.DotLine)
    p.setPen(grid_pen)
    for i in range(1, 4):
        y = i * 32
        p.drawLine(10, y, 118, y)

    # Pulse line
    pen = QPen(QColor(COLORS["seafoam"]), 3)
    p.setPen(pen)
    points = [(10, 90), (25, 50), (40, 75), (55, 20), (70, 65), (85, 35), (100, 55), (118, 30)]
    for i in range(len(points) - 1):
        p.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

    # Dot highlight
    p.setBrush(QColor(COLORS["seafoam"]))
    p.setPen(Qt.NoPen)
    for pt in points:
        p.drawEllipse(QPoint(pt[0], pt[1]), 3, 3)

    p.end()
    return pm


def _draw_harbor() -> QPixmap:
    """Harbor File Manager — folder with anchor."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["slate_navy"])

    # Folder shape
    folder_color = QColor(COLORS["amber"])
    p.setBrush(folder_color)
    p.setPen(Qt.NoPen)
    # Tab
    p.drawRoundedRect(25, 28, 40, 12, 3, 3)
    # Body
    p.drawRoundedRect(20, 36, 88, 62, 4, 4)

    # Anchor inside folder
    p.setPen(QPen(QColor(COLORS["void_black"]), 3))
    cx, cy = 64, 72
    p.drawLine(cx, cy - 18, cx, cy + 10)  # vertical
    p.drawLine(cx - 14, cy + 5, cx + 14, cy + 5)  # crossbar
    p.drawArc(cx - 12, cy - 10, 24, 20, 0, 180 * 16)  # arc top

    p.end()
    return pm


def _draw_tide() -> QPixmap:
    """Tide Terminal — command prompt."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["void_black"])

    # Terminal window border
    p.setPen(QPen(QColor(COLORS["border"]), 2))
    p.drawRect(10, 10, 108, 108)

    # Prompt lines
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(COLORS["seafoam"]))
    p.drawRect(20, 28, 60, 4)
    p.setBrush(QColor(COLORS["hd_white"]))
    p.drawRect(85, 28, 30, 4)

    p.setBrush(QColor(COLORS["seafoam"]))
    p.drawRect(20, 42, 60, 4)
    p.setBrush(QColor(COLORS["hd_white"]))
    p.drawRect(85, 42, 20, 4)

    # Cursor blink
    p.setBrush(QColor(COLORS["seafoam"]))
    p.drawRect(20, 56, 8, 4)
    p.drawRect(36, 56, 40, 4)

    p.end()
    return pm


def _draw_anchor() -> QPixmap:
    """Anchor Settings — gear."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    # Gear teeth
    center = 64
    outer_r = 42
    inner_r = 28
    pen = QPen(QColor(COLORS["seafoam"]), 8)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    import math
    teeth = 8
    for i in range(teeth * 2):
        angle = (i * math.pi) / teeth - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        x = center + int(r * math.cos(angle))
        y = center + int(r * math.sin(angle))
        if i == 0:
            p.drawPoint(x, y)
            continue
        prev_angle = ((i - 1) * math.pi) / teeth - math.pi / 2
        prev_r = outer_r if (i - 1) % 2 == 0 else inner_r
        px = center + int(prev_r * math.cos(prev_angle))
        py = center + int(prev_r * math.sin(prev_angle))
        p.drawLine(px, py, x, y)

    # Inner circle
    p.setBrush(QColor(COLORS["deep_navy"]))
    p.drawEllipse(QPoint(center, center), inner_r - 8, inner_r - 8)

    p.end()
    return pm


def _draw_kraken() -> QPixmap:
    """Kraken AI — low-poly sea monster with tentacles and a coral eye."""
    from PySide6.QtGui import QPainterPath

    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    # ── Low-poly kraken head ──
    head = [
        QPoint(34, 34), QPoint(56, 28), QPoint(80, 30), QPoint(98, 44),
        QPoint(94, 62), QPoint(72, 74), QPoint(46, 72), QPoint(32, 54),
    ]
    p.setPen(QPen(QColor(COLORS["seafoam"]), 4))
    p.setBrush(QColor(COLORS["slate_navy"]))
    p.drawPolygon(head)

    # ── Tentacles sweeping below the head ──
    tentacles = [
        (QPointF(44, 70), QPointF(34, 86), QPointF(28, 100), QPointF(44, 110)),
        (QPointF(62, 75), QPointF(58, 92), QPointF(72, 102), QPointF(88, 104)),
        (QPointF(84, 70), QPointF(92, 84), QPointF(102, 94), QPointF(98, 108)),
    ]
    p.setPen(QPen(QColor(COLORS["seafoam"]), 5))
    p.setBrush(Qt.NoBrush)
    for start, c1, c2, end in tentacles:
        path = QPainterPath(start)
        path.cubicTo(c1, c2, end)
        p.drawPath(path)

    # ── Tentacle tips (coral suckers) ──
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(COLORS["coral"]))
    for tip in (QPoint(44, 110), QPoint(88, 104), QPoint(98, 108)):
        p.drawEllipse(tip, 5, 5)

    # ── Coral eye + seafoam pupil ──
    p.setBrush(QColor(COLORS["coral"]))
    p.drawEllipse(QPoint(72, 50), 7, 7)
    p.setBrush(QColor(COLORS["hd_white"]))
    p.drawEllipse(QPoint(70, 48), 3, 3)

    # ── Crown spikes across the head ──
    p.setPen(QPen(QColor(COLORS["amber"]), 3))
    p.drawLine(48, 32, 52, 44)
    p.drawLine(64, 29, 66, 42)
    p.drawLine(82, 31, 80, 44)

    p.end()
    return pm


def _draw_nautilus() -> QPixmap:
    """Nautilus OS — anchor/ship wheel."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["abyss_navy"])

    # Outer ring
    pen = QPen(QColor(COLORS["seafoam"]), 4)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(20, 20, 88, 88)

    # Spokes (8 directions)
    import math
    center = 64
    for i in range(8):
        angle = i * math.pi / 4
        ex = center + int(38 * math.cos(angle))
        ey = center + int(38 * math.sin(angle))
        sx = center + int(12 * math.cos(angle))
        sy = center + int(12 * math.sin(angle))
        p.drawLine(sx, sy, ex, ey)

    # Inner circle
    p.setBrush(QColor(COLORS["abyss_navy"]))
    p.drawEllipse(QPoint(center, center), 14, 14)

    # Center dot
    p.setBrush(QColor(COLORS["seafoam"]))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPoint(center, center), 6, 6)

    p.end()
    return pm


def _draw_cinema() -> QPixmap:
    """Cinema — film frame with play button."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["abyss_navy"])

    # Film strip / frame
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(COLORS["deep_navy"]))
    p.drawRoundedRect(14, 22, 100, 84, 4, 4)

    # Sprocket holes
    p.setBrush(QColor(COLORS["abyss_navy"]))
    for y in (28, 96):
        for x in range(22, 112, 14):
            p.drawRect(x, y, 6, 4)

    # Play triangle
    p.setBrush(QColor(COLORS["seafoam"]))
    p.drawPolygon([QPoint(52, 46), QPoint(82, 64), QPoint(52, 82)])

    # Bottom accent bar
    p.setBrush(QColor(COLORS["coral"]))
    p.drawRect(30, 108, 68, 4)

    p.end()
    return pm


def _draw_logbook() -> QPixmap:
    """Logbook — open notebook with a pen stroke."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    # Book pages
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(COLORS["slate_navy"]))
    p.drawRoundedRect(24, 20, 80, 88, 3, 3)
    # Spine line
    p.fillRect(62, 20, 4, 88, QColor(COLORS["deep_navy"]))
    # Text lines (left page)
    p.setBrush(QColor(COLORS["seafoam"]))
    for y in range(34, 78, 8):
        p.drawRect(32, y, 24, 3)
    # Right page highlights
    p.setBrush(QColor(COLORS["amber"]))
    p.drawRect(72, 34, 22, 3)
    p.drawRect(72, 42, 22, 3)
    p.setBrush(QColor(COLORS["text_muted"]))
    for y in range(50, 78, 8):
        p.drawRect(72, y, 22, 3)

    # Pen diagonal
    p.setPen(QPen(QColor(COLORS["coral"]), 4))
    p.drawLine(96, 100, 112, 84)
    p.setBrush(QColor(COLORS["coral"]))
    p.setPen(Qt.NoPen)
    p.drawEllipse(112, 80, 8, 8)

    p.end()
    return pm


def _draw_mariner() -> QPixmap:
    """Mariner — compass with mathematical symbols."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["slate_navy"])

    # Compass ring
    p.setPen(QPen(QColor(COLORS["seafoam"]), 4))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(24, 24, 80, 80)

    # Cardinal ticks
    p.setPen(QPen(QColor(COLORS["hd_white"]), 3))
    for angle_deg in (0, 90, 180, 270):
        import math
        a = math.radians(angle_deg)
        p.drawLine(64 + int(30 * math.cos(a)), 64 + int(30 * math.sin(a)),
                   64 + int(40 * math.cos(a)), 64 + int(40 * math.sin(a)))

    # Math glyphs around dial
    p.setPen(QPen(QColor(COLORS["amber"]), 3))
    p.drawLine(52, 42, 76, 42)
    p.drawLine(64, 34, 64, 50)
    p.setPen(QPen(QColor(COLORS["coral"]), 3))
    p.drawEllipse(QPoint(64, 64), 12, 12)

    # Center needle
    p.setPen(QPen(QColor(COLORS["seafoam"]), 3))
    p.drawLine(64, 64, 64, 40)
    p.setBrush(QColor(COLORS["seafoam"]))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPoint(64, 64), 5, 5)

    p.end()
    return pm


def _draw_anchor_display() -> QPixmap:
    """Anchor Settings — Display tab: monitor."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    pen = QPen(QColor(COLORS["seafoam"]), 4)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(20, 26, 88, 56, 4, 4)
    p.drawLine(48, 96, 80, 96)
    p.drawLine(64, 82, 64, 96)
    p.drawLine(40, 108, 88, 108)

    p.setBrush(QColor(COLORS["amber"]))
    p.setPen(Qt.NoPen)
    p.drawEllipse(96, 42, 10, 10)

    p.end()
    return pm


def _draw_anchor_network() -> QPixmap:
    """Anchor Settings — Network tab: globe with orbit."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    pen = QPen(QColor(COLORS["seafoam"]), 4)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(30, 30, 68, 68)

    p.drawEllipse(36, 54, 56, 20)
    p.drawLine(64, 30, 64, 98)
    p.drawLine(30, 64, 98, 64)

    p.setBrush(QColor(COLORS["coral"]))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPoint(88, 46), 7, 7)

    p.end()
    return pm


def _draw_anchor_audio() -> QPixmap:
    """Anchor Settings — Audio tab: speaker with waves."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    p.setPen(QPen(QColor(COLORS["seafoam"]), 4))
    p.setBrush(QColor(COLORS["seafoam_deep"]))
    p.drawRect(26, 44, 22, 40)
    p.drawPolygon(
        [QPoint(48, 44), QPoint(74, 24), QPoint(74, 104), QPoint(48, 84)]
    )

    p.setPen(QPen(QColor(COLORS["amber"]), 4))
    p.setBrush(Qt.NoBrush)
    p.drawArc(80, 36, 36, 56, -60 * 16, 120 * 16)
    p.drawArc(86, 30, 48, 68, -60 * 16, 120 * 16)

    p.end()
    return pm


def _draw_anchor_theme() -> QPixmap:
    """Anchor Settings — Theme tab: paint palette."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    p.setPen(Qt.NoPen)
    p.setBrush(QColor(COLORS["slate_navy"]))
    path = [
        QPoint(50, 30), QPoint(92, 30), QPoint(112, 52), QPoint(110, 86),
        QPoint(90, 104), QPoint(52, 104), QPoint(30, 86), QPoint(30, 52),
    ]
    p.drawPolygon(path)

    dots = [
        (50, 56, COLORS["seafoam"]),
        (72, 46, COLORS["coral"]),
        (90, 62, COLORS["amber"]),
        (70, 78, COLORS["hd_white"]),
    ]
    for x, y, color in dots:
        p.setBrush(QColor(color))
        p.drawEllipse(QPoint(x, y), 6, 6)

    p.end()
    return pm


def _draw_anchor_about() -> QPixmap:
    """Anchor Settings — About tab: info badge."""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    p.setPen(QPen(QColor(COLORS["seafoam"]), 4))
    p.setBrush(QColor(COLORS["seafoam_deep"]))
    p.drawEllipse(28, 28, 72, 72)

    p.setPen(QPen(QColor(COLORS["seafoam"]), 5))
    p.drawLine(64, 58, 64, 86)
    p.drawLine(64, 40, 64, 44)

    p.end()
    return pm


def _draw_reef() -> QPixmap:
    """Reef Messenger — coral message bubble with seafoam typing dots."""
    from PySide6.QtCore import QPointF, QRectF
    from PySide6.QtGui import QPainterPath

    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_base(p, 128, 128, COLORS["deep_navy"])

    # Message bubble with tail
    bubble = QPainterPath()
    bubble.addRoundedRect(QRectF(20, 26, 88, 58), 14, 14)
    bubble.moveTo(34, 84)
    bubble.lineTo(22, 106)
    bubble.lineTo(56, 84)
    bubble.closeSubpath()
    p.setPen(QPen(QColor(COLORS["coral"]), 5))
    p.setBrush(QColor(COLORS["slate_navy"]))
    p.drawPath(bubble)

    # Typing dots
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(COLORS["seafoam"]))
    for x in (40, 57, 74):
        p.drawEllipse(QPointF(x, 55), 5, 5)

    # Coral wave underline
    p.setPen(QPen(QColor(COLORS["coral"]), 4))
    p.setBrush(Qt.NoBrush)
    wave = QPainterPath(QPointF(26, 116))
    wave.quadTo(QPointF(42, 108), QPointF(58, 116))
    wave.quadTo(QPointF(74, 124), QPointF(90, 116))
    p.drawPath(wave)

    p.end()
    return pm


# ═══════════════════════════════════════════════════════════════
#  GENERATOR MAP
# ═══════════════════════════════════════════════════════════════

_GENERATORS = {
    "abyssal":  _draw_abyssal,
    "surfline": _draw_surfline,
    "riptide":  _draw_riptide,
    "cinema":   _draw_cinema,
    "logbook":  _draw_logbook,
    "mariner":  _draw_mariner,
    "current":  _draw_current,
    "harbor":   _draw_harbor,
    "tide":     _draw_tide,
    "anchor":   _draw_anchor,
    "kraken":   _draw_kraken,
    "nautilus": _draw_nautilus,
    "reef":     _draw_reef,
    "anchor_display": _draw_anchor_display,
    "anchor_network": _draw_anchor_network,
    "anchor_audio": _draw_anchor_audio,
    "anchor_theme": _draw_anchor_theme,
    "anchor_about": _draw_anchor_about,
}

# Cache of generated pixmaps
_cache: dict[str, QPixmap] = {}


def ensure_all_logos():
    """Pre-generate all app logos to disk."""
    os.makedirs(LOGOS_DIR, exist_ok=True)
    for app_id, gen in _GENERATORS.items():
        path = _logo_path(app_id)
        if not os.path.exists(path):
            pix = gen()
            pix.save(path, "PNG")


def _disk_logo(app_id: str) -> QPixmap | None:
    """Load a cached logo PNG from disk (AI-generated assets land here)."""
    path = _logo_path(app_id)
    if not os.path.exists(path):
        return None
    pix = QPixmap(path)
    return None if pix.isNull() else pix


def get_logo(app_id: str, size: int = None) -> QIcon:
    """Get an app logo as QIcon. Prefers the disk cache (assets/logos/), then
    generates programmatically. Caches in memory."""
    if app_id not in _cache:
        pix = _disk_logo(app_id)
        if pix is None:
            gen = _GENERATORS.get(app_id)
            if gen:
                pix = gen()
            else:
                # Fallback: simple colored square with letter
                pix = QPixmap(128, 128)
                pix.fill(Qt.transparent)
                p = QPainter(pix)
                p.fillRect(0, 0, 128, 128, QColor(COLORS["slate_navy"]))
                p.setPen(QColor(COLORS["seafoam"]))
                font = QFont("JetBrains Mono", 50, QFont.Bold)
                p.setFont(font)
                p.drawText(pix.rect(), Qt.AlignCenter, app_id[0].upper())
                p.end()
        _cache[app_id] = pix

    pix = _cache[app_id]
    if size:
        pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return QIcon(pix)


def get_pixmap(app_id: str, size: int = 48) -> QPixmap:
    """Get an app logo as QPixmap at the given size."""
    icon = get_logo(app_id)
    return icon.pixmap(size, size)
