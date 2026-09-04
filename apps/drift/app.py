"""Drift — Email Client"""

from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from core.theme import COLORS, FONTS


class DriftWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drift")
        self.resize(860, 620)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_dark']};
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Drift — Email")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            color: {COLORS['ice']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_title']}px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(label)
