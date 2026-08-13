#!/usr/bin/env python3
"""
Cinema — Nautilus Media Center

Fully local, offline movie & TV library. Import your own media into My Media,
browse the poster grid, and watch with a full-screen QtMultimedia player.

Launch:  py -3.13 apps/Cinema/main.py
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import QApplication

try:
    from core.icons import get_logo
    from core.logger import get_logger
    from core.theme import FONTS, create_nautilus_palette, get_global_stylesheet
except ImportError:
    FONTS = {"ui": "Segoe UI", "mono": "JetBrains Mono", "size_md": 12}

    def get_global_stylesheet():
        return ""
    def create_nautilus_palette():
        return QPalette()
    def get_logo(*a, **k):
        return None


def main():
    try:
        log = get_logger("APP")
        log.info("Cinema Media Center starting")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Cinema")
    app.setOrganizationName("Nautilus")

    try:
        app.setWindowIcon(get_logo("cinema"))
    except Exception:
        pass

    try:
        app.setPalette(create_nautilus_palette())
        app.setStyleSheet(get_global_stylesheet())
    except Exception:
        pass

    font = QFont()
    font.setFamilies([FONTS.get("ui", "Segoe UI"), FONTS.get("mono", "JetBrains Mono")])
    font.setPointSize(FONTS.get("size_md", 12))
    app.setFont(font)

    from apps.Cinema.src.window import CinemaWindow

    window = CinemaWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
