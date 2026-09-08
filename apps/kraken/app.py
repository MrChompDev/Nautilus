"""Kraken — AI Assistant"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from core.theme import COLORS, FONTS


class KrakenWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kraken")
        self.resize(800, 600)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_dark']};
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Kraken — AI Assistant")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            color: {COLORS['ice']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_title']}px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(label)
