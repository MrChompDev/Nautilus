#!/usr/bin/env python3
"""
Kraken AI — Nautilus OS desktop app.

Deep sea creature themed AI: four specialized models (Kraken, Leviathan,
Charybdis, Megalodon) with a ChatGPT/Claude-style desktop interface.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

try:
    from core.qt_env import setup_qt_environment
except ImportError:
    def setup_qt_environment():
        pass

setup_qt_environment()

from PySide6.QtGui import QFont  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

try:
    from core.logger import get_logger  # noqa: E402
except Exception:
    get_logger = None

try:
    from core.theme import FONTS, create_nautilus_palette, get_global_stylesheet  # noqa: E402
except ImportError:
    FONTS = {"ui": "Segoe UI", "mono": "JetBrains Mono", "size_md": 12}

    def create_nautilus_palette():
        from PySide6.QtGui import QPalette
        return QPalette()

    def get_global_stylesheet():
        return ""

from apps.kraken.core.config import KrakenConfig  # noqa: E402
from apps.kraken.ui.main_window import KrakenWindow  # noqa: E402


def main():
    if get_logger:
        try:
            log = get_logger("APP")
            log.info("Kraken AI desktop starting")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Kraken AI")
    app.setOrganizationName("Nautilus")

    try:
        from core.icons import get_logo
        app.setWindowIcon(get_logo("kraken"))
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

    cfg = KrakenConfig.load()
    window = KrakenWindow(cfg)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
