from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from apps.Abyssal.src.ui.styles import AbyssalTheme


class PanelWidget(QWidget):
    def __init__(self, title: str = "Panel", parent=None):
        super().__init__(parent)
        self._title = title
        self.setStyleSheet(f"background-color: {AbyssalTheme.BG_DARK};")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(30)
        header.setFrameShape(QFrame.StyledPanel)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {AbyssalTheme.TITLE_BAR};
                border-bottom: 1px solid {AbyssalTheme.BORDER};
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 4, 10, 4)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {AbyssalTheme.TEXT_DIM};
            font-size: 10px;
            font-weight: bold;
        """)
        title_label.setFont(QFont("Segoe UI", 9))
        header_layout.addWidget(title_label)

        outer.addWidget(header)

    def set_title(self, title: str) -> None:
        self._title = title

    def get_title(self) -> str:
        return self._title