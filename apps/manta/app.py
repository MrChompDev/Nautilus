"""Manta — Presentation Builder"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from core.theme import COLORS, FONTS


class MantaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manta")
        self.resize(960, 640)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_dark']};
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Manta — Presentations")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            color: {COLORS['ice']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_title']}px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(label)
