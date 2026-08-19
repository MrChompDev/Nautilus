"""Nautilus OS - Shell"""

import sys
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Add the parent directory to sys.path
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt, QTimer
from core.theme import COLORS, FONTS, RADIUS_MD
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton


class Topbar(Frame):
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

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 0, 16, 0)

        #Left: app name
        name = QLabel("Nautilus")
        name.setStyleSheet(f"""
        color: {COLORS['text_dark']};
        font-family: {FONTS['mono']};
        font-size: {FONTS['size_sm']};
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
        font-family: {FONTS['mono']};
        font-size: {FONTS['size_sm']};
        background: transparent;
        border: none;
        """)
        layout.addWidget(self.clock)

        # Update clock every second
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()  # Initial update

        def update_clock(self):
            from pySide6.QtCore import QDateTime
            now = QDatetime.currentDateTime()
            self.clock.setText(now.toString("hh:mm:ss AP"))


class NautilusShell(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nautilus OS Shell")
        self.resize(1280, 720)

        # Set background color
        self.setStyleSheet(f"""
        Qmainwindow {{
            background-color: {COLORS['bg_light']};
        }}
        """)

        # Center label
        label = QLabel("Nautilus OS")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
        color: {COLORS['text']};
        font-family: {FONTS['ui']};
        font-size: {FONTS['size_title']};
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


        