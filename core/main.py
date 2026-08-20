"""Nautilus OS - Shell"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QFrame, QHBoxLayout, QPushButton, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QDateTime
from core.theme import COLORS, FONTS, RADIUS_MD, RADIUS_SM


class TopBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(212, 200, 176, 200);
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_MD};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        # Left: app name
        name = QLabel("NAUTILUS")
        name.setStyleSheet(f"""
            color: {COLORS['text_dark']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            font-weight: bold;
            letter-spacing: 3px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(name)

        layout.addStretch()

        # Right: clock
        self.clock = QLabel("")
        self.clock.setStyleSheet(f"""
            color: {COLORS['text_dark']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.clock)

        # Update clock every second
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()

    def update_clock(self):
        now = QDateTime.currentDateTime()
        self.clock.setText(now.toString("hh:mm AP"))

class Dock(QFrame):
    def __init__(self, on_launch):
        (super().__init__())
        self.on_launch = on_launch
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(212, 200, 176, 200);
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_MD};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # App buttons
        apps = ["Surfline", "Abyssal", "Kraken"]
        for app_name in apps:
            btn = QPushButton(app_name)
            btn.setFixedSize(80, 40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_mid']};
                    color: {COLORS['text_dark']};
                    border: 1px solid {COLORS['border']};
                    border-radius: {RADIUS_SM};
                    font-family: "{FONTS['mono']}";
                    font-size: {FONTS['size_xs']}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['hover']};
                    border: 1px solid {COLORS['border_light']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['pressed']};
                }}
            """)
            btn.clicked.connect(lambda checked, name=app_name: self.on_launch(name))
            layout.addWidget(btn)

class NautilusShell(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nautilus OS")
        self.resize(1280, 720)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_light']};
            }}
        """)
        # Central Widget wit layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        # Top bar
        layout.addWidget(TopBar())
        
        # Content area
        label = QLabel("Nautilus OS")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            color: {COLORS['text_dark']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_title']}px;
            font-weight: bold;
        """)
        layout.addWidget(label)

        # Dock
        dock = Dock(on_launch=self.launch_app)
        dock.setParent(self)
        dock.move(440, 650)
        dock.show()

    def launch_app(self, app_name):
        if app_name == "Surfline":
            from apps.surfline.app import SurflineWindow
            self.browser = SurflineWindow()
            self.browser.show()

        else:
            print(f"Launching {app_name}...")



def main():
    app = QApplication(sys.argv)
    shell = NautilusShell()
    shell.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
