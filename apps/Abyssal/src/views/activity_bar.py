from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout, QWidget

from apps.Abyssal.src.ui.styles import AbyssalTheme

ICONS = {
    "explorer": "\u25B6",
    "search": "\u01d11",
    "git": "\u2692",
    "extensions": "\u02b6",
    "settings": "\u2699",
}


class ActivityBarButton(QPushButton):
    def __init__(self, icon_char: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.setText(icon_char)
        self.setCheckable(True)
        self.setFixedWidth(48)
        self.setFixedHeight(48)
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe MDL2 Assets", 14))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {AbyssalTheme.TEXT_DIM};
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0px;
                padding: 0;
                margin: 0;
            }}
            QPushButton:hover {{
                color: {AbyssalTheme.TEXT};
                background-color: {AbyssalTheme.PANEL_HOVER};
                border-left-color: transparent;
            }}
            QPushButton:checked {{
                color: {AbyssalTheme.ACCENT_LIGHT};
                border-left: 3px solid {AbyssalTheme.ACCENT};
                background-color: transparent;
            }}
        """)


class ActivityBar(QWidget):
    panel_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(48)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AbyssalTheme.TITLE_BAR};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(4)

        self.buttons = {}

        for name, icon in ICONS.items():
            btn = ActivityBarButton(icon, name.capitalize())
            btn.clicked.connect(lambda checked, n=name: self._on_click(n))
            self.buttons[name] = btn
            layout.addWidget(btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet(f"color: {AbyssalTheme.BORDER}; margin: 4px 12px;")
        layout.addWidget(sep)

        settings_btn = ActivityBarButton(ICONS["settings"], "Settings")
        settings_btn.clicked.connect(lambda: self._on_click("settings"))
        self.buttons["settings"] = settings_btn
        layout.addWidget(settings_btn)

        layout.addStretch()

    def _on_click(self, name: str) -> None:
        for n, btn in self.buttons.items():
            if n != name:
                btn.setChecked(False)
        self.panel_changed.emit(name)

    def activate_panel(self, name: str) -> None:
        for n, btn in self.buttons.items():
            btn.setChecked(n == name)
        self.panel_changed.emit(name)