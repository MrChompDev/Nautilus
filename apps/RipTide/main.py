"""Riptide Audio - Unified Music & SFX Platform
Version 3.0
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from apps.RipTide.ui.main_window import MainWindow
from apps.RipTide.ui.styles import apply_dark_theme


def main():
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
