import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from apps.Abyssal.application import AbyssalMainWindow

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")

if __name__ == "__main__":
    # Ensure config directory exists
    os.makedirs(CONFIG_DIR, exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Abyssal")
    app.setOrganizationName("Nautilus")
    app.setFont(QFont("JetBrains Mono", 10))

    try:
        from core.icons import get_logo
        app.setWindowIcon(get_logo("abyssal"))
    except Exception:
        pass

    try:
        from core.theme import create_nautilus_palette, get_global_stylesheet
        app.setPalette(create_nautilus_palette())
        app.setStyleSheet(get_global_stylesheet())
    except Exception:
        pass

    window = AbyssalMainWindow()
    window.show()

    # Add application cleanup
    def cleanup():
        print("Abyssal Editor shutting down...")

    app.lastWindowClosed.connect(cleanup)

    sys.exit(app.exec())
