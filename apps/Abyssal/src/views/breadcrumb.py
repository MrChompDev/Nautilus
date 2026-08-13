from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from apps.Abyssal.src.ui.styles import AbyssalTheme


class BreadcrumbBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(26)
        self.setStyleSheet(f"""
            background-color: {AbyssalTheme.BREADCRUMB};
            border-bottom: 1px solid {AbyssalTheme.BORDER};
        """)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 0, 8, 0)
        self.layout.setSpacing(2)

        self.labels = []
        self._clear()

    def set_path(self, file_path: str) -> None:
        self._clear()
        if not file_path:
            return

        parts = file_path.replace("\\", "/").split("/")
        for i, part in enumerate(parts):
            if i > 0:
                sep = QLabel(" > ")
                sep.setStyleSheet(f"color: {AbyssalTheme.TEXT_MUTED}; font-size: 10px;")
                sep.setFont(QFont("Segoe UI", 9))
                self.layout.addWidget(sep)
                self.labels.append(sep)

            lbl = QLabel(part)
            is_last = i == len(parts) - 1
            color = AbyssalTheme.TEXT if is_last else AbyssalTheme.TEXT_DIM
            lbl.setStyleSheet(f"color: {color}; font-size: 10px;")
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setCursor(Qt.PointingHandCursor)
            self.layout.addWidget(lbl)
            self.labels.append(lbl)

        self.layout.addStretch()

    def _clear(self) -> None:
        for lbl in self.labels:
            lbl.setParent(None)
            lbl.deleteLater()
        self.labels.clear()
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()