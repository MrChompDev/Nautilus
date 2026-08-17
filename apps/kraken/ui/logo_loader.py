"""Kraken AI — SVG logo loader.

Loads creature logos from the logos/ directory and returns QPixmap objects.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget

_LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logos")


def logo_path(creature_id: str) -> str:
    return os.path.join(_LOGO_DIR, f"{creature_id}.svg")


def load_logo_pixmap(creature_id: str, size: int = 48) -> QPixmap:
    path = logo_path(creature_id)
    if not os.path.exists(path):
        return QPixmap(size, size)
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def load_logo_widget(creature_id: str, size: int = 48) -> QSvgWidget:
    path = logo_path(creature_id)
    widget = QSvgWidget(path)
    widget.setFixedSize(size, size)
    return widget
