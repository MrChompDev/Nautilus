"""Nautilus OS - Shell"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QFrame, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer, QDateTime
from core.theme import COLORS, FONTS, RADIUS_MD


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

        # Center label
        label = QLabel("Nautilus OS")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            color: {COLORS['text_dark']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_title']}px;
            font-weight: bold;
        """)
        self.setCentralWidget(label)


def main():
    app = QApplication(sys.argv)
    shell = NautilusShell()
    shell.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
