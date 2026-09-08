"""Nautilus OS - Shell"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QScrollArea, QVBoxLayout, QWidget

from core.launcher import APP_MANIFEST, DOCK_APPS, launch_app
from core.profile import Profile
from core.theme import COLORS, FONTS, RADIUS_MD

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")

_profile = Profile()
_profile.check_daily_login()


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

        # Gamification display
        self.level_label = QLabel()
        self.level_label.setStyleSheet(f"""
            color: {COLORS['gold']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.level_label)

        self.xp_bar = QLabel()
        self.xp_bar.setFixedWidth(80)
        self.xp_bar.setStyleSheet(f"""
            color: {COLORS['xp_blue']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.xp_bar)

        spacer = QLabel("  ")
        spacer.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(spacer)

        self.coin_label = QLabel()
        self.coin_label.setStyleSheet(f"""
            color: {COLORS['gold']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.coin_label)

        spacer2 = QLabel("  ")
        spacer2.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(spacer2)

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
        timer.timeout.connect(self.update_gamification)
        timer.start(1000)
        self.update_clock()
        self.update_gamification()

    def update_clock(self):
        now = QDateTime.currentDateTime()
        self.clock.setText(now.toString("hh:mm AP"))

    def update_gamification(self):
        global _profile
        _profile = Profile()
        self.level_label.setText(f"\u2693 Lv.{_profile.level}")
        self.coin_label.setText(f"\U0001FA99 {_profile.coins}")
        self.xp_bar.setText(f"{_profile.xp}xp")


class AppButton(QFrame):
    def __init__(self, name, icon_file, on_launch):
        super().__init__()
        self.name = name
        self.on_launch = on_launch
        self.setFixedSize(72, 68)
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
        layout.setContentsMargins(0, 4, 0, 2)
        layout.setSpacing(2)

        icon_label = QLabel()
        icon_path = os.path.join(ICONS_DIR, icon_file)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("?")
            icon_label.setStyleSheet(f"color: {COLORS['teal']}; font-size: 18px;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_label)

        label = QLabel(name)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            color: {COLORS['ice']};
            font-family: "{FONTS['mono']}";
            font-size: 8px;
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
        self.setFixedHeight(85)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(10, 22, 40, 180);
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_MD};
            }}
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        inner = QWidget()
        layout = QHBoxLayout(inner)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        for app_name in DOCK_APPS:
            info = APP_MANIFEST.get(app_name)
            if info:
                btn = AppButton(app_name, info["icon"], on_launch)
                layout.addWidget(btn)

        layout.addStretch()
        scroll.setWidget(inner)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)


class WallpaperWidget(QWidget):
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
        self._windows = {}

        self.wallpaper = WallpaperWidget()
        self.setCentralWidget(self.wallpaper)

        self.main_layout = QVBoxLayout(self.wallpaper)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.main_layout.addWidget(TopBar())
        self.main_layout.addStretch()

        dock = Dock(on_launch=self.launch_app)
        dock.setFixedWidth(960)
        dock.setParent(self.wallpaper)

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
        window = launch_app(app_name, self)
        if window is not None:
            self._windows[app_name] = window


def main():
    app = QApplication(sys.argv)
    shell = NautilusShell()
    shell.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
