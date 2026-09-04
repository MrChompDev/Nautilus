"""Nautilus OS - Shell"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFrame, QHBoxLayout,
    QPushButton, QWidget, QVBoxLayout
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QPixmap, QPainter, QIcon
from core.theme import COLORS, FONTS, RADIUS_MD, RADIUS_SM

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")


class TopBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(10, 22, 40, 180);
                border-bottom: 1px solid {COLORS['border']};
                border-radius: 0px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        name = QLabel("NAUTILUS")
        name.setStyleSheet(f"""
            color: {COLORS['ice']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            font-weight: bold;
            letter-spacing: 3px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(name)

        layout.addStretch()

        self.clock = QLabel("")
        self.clock.setStyleSheet(f"""
            color: {COLORS['ice']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.clock)

        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()

    def update_clock(self):
        now = QDateTime.currentDateTime()
        self.clock.setText(now.toString("hh:mm AP"))


class AppButton(QFrame):
    """Icon + label button for the dock."""

    def __init__(self, name, icon_file, on_launch):
        super().__init__()
        self.name = name
        self.on_launch = on_launch
        self.setFixedSize(80, 72)
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border-radius: 10px;
            }
            QFrame:hover {
                background: rgba(23, 165, 188, 40);
            }
        """)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        # Icon
        icon_label = QLabel()
        icon_path = os.path.join(ICONS_DIR, icon_file)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("?")
            icon_label.setStyleSheet(f"color: {COLORS['teal']}; font-size: 20px;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_label)

        # Label
        label = QLabel(name)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            color: {COLORS['ice']};
            font-family: "{FONTS['mono']}";
            font-size: 9px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(label)

    def mousePressEvent(self, event):
        self.on_launch(self.name)


class Dock(QFrame):
    def __init__(self, on_launch):
        super().__init__()
        self.on_launch = on_launch
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(10, 22, 40, 180);
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_MD};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        apps = [
            ("Surfline",   "jellyfish.svg"),
            ("Abyssal",    "anglerfish.svg"),
            ("Kraken",     "octopus.svg"),
            ("Logbook",    "turtle.svg"),
            ("Trench",     "narwhal.svg"),
            ("Manta",      "manta.svg"),
            ("Coral",      "crab.svg"),
            ("Drift",      "seahorse.svg"),
        ]
        for app_name, icon_file in apps:
            btn = AppButton(app_name, icon_file, on_launch)
            layout.addWidget(btn)


class WallpaperWidget(QWidget):
    """Renders the wallpaper as a background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap(os.path.join(ASSETS_DIR, "Wallpaper.png"))

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillRect(self.rect(), QColor(COLORS['bg_dark']))
        painter.end()


class NautilusShell(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nautilus OS")
        self.resize(1280, 720)

        # Wallpaper background
        self.wallpaper = WallpaperWidget()
        self.setCentralWidget(self.wallpaper)

        # Layout on top of wallpaper
        self.main_layout = QVBoxLayout(self.wallpaper)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Top bar
        self.main_layout.addWidget(TopBar())

        # Content area (spacer)
        self.main_layout.addStretch()

        # Dock
        dock = Dock(on_launch=self.launch_app)
        dock.setFixedWidth(720)
        dock.setParent(self.wallpaper)

        # Position dock at bottom center
        self._dock = dock
        self._position_dock()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_dock()

    def _position_dock(self):
        if hasattr(self, '_dock') and self._dock:
            x = (self.width() - self._dock.width()) // 2
            y = self.height() - self._dock.height() - 16
            self._dock.move(x, y)
            self._dock.show()

    def launch_app(self, app_name):
        if app_name == "Surfline":
            from apps.surfline.app import SurflineWindow
            self._surfline = SurflineWindow()
            self._surfline.show()
        elif app_name == "Abyssal":
            from apps.abyssal.app import AbyssalWindow
            self._abyssal = AbyssalWindow()
            self._abyssal.show()
        elif app_name == "Kraken":
            from apps.kraken.app import KrakenWindow
            self._kraken = KrakenWindow()
            self._kraken.show()
        elif app_name == "Logbook":
            from apps.logbook.app import LogbookWindow
            self._logbook = LogbookWindow()
            self._logbook.show()
        elif app_name == "Trench":
            from apps.trench.app import TrenchWindow
            self._trench = TrenchWindow()
            self._trench.show()
        elif app_name == "Manta":
            from apps.manta.app import MantaWindow
            self._manta = MantaWindow()
            self._manta.show()
        elif app_name == "Coral":
            from apps.coral.app import CoralWindow
            self._coral = CoralWindow()
            self._coral.show()
        elif app_name == "Drift":
            from apps.drift.app import DriftWindow
            self._drift = DriftWindow()
            self._drift.show()


def main():
    app = QApplication(sys.argv)
    shell = NautilusShell()
    shell.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
