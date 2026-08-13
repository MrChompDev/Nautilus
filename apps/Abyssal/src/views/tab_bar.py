import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QScrollArea, QWidget

from apps.Abyssal.src.ui.styles import AbyssalTheme

LANG_ICONS = {
    "python": "\u03C6",
    "javascript": "JS",
    "typescript": "TS",
    "html": "\u266E",
    "css": "\u266F",
    "c": "C",
    "cpp": "C+",
    "bash": "\u25B6",
    "json": "{}",
    "yaml": "\u2261",
    "markdown": "\u2261",
    "xml": "</>",
    "text": "\u00B6",
    "rust": "\u0391",
    "go": "\u2207",
    "java": "J",
    "ruby": "R",
    "sql": "S",
    "toml": "\u2261",
    "ini": "\u2261",
}


class TabButton(QPushButton):
    clicked_close = Signal(str)

    def __init__(self, file_path: str, language: str = "text", parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.language = language
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(35)
        self.setMinimumWidth(80)
        self.setMaximumWidth(180)
        self._update_text()
        self.setStyleSheet(self._style(False))
        self.clicked.connect(lambda: self.parent().select_tab(self.file_path))

    def _update_text(self) -> None:
        name = os.path.basename(self.file_path) if self.file_path else "untitled"
        icon = LANG_ICONS.get(self.language, "\u00B6")
        self.setText(f" {icon}  {name}  ")

    def set_active(self, active: bool) -> None:
        self.blockSignals(True)
        self.setChecked(active)
        self.blockSignals(False)
        self.setStyleSheet(self._style(active))

    def _style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background-color: {AbyssalTheme.ACTIVE_TAB};
                    color: {AbyssalTheme.TEXT};
                    border: none;
                    border-top: 2px solid {AbyssalTheme.ACCENT};
                    border-bottom: 1px solid {AbyssalTheme.BORDER};
                    border-left: 1px solid {AbyssalTheme.BORDER};
                    border-right: 1px solid {AbyssalTheme.BORDER};
                    padding: 2px 8px;
                    font-size: 11px;
                    text-align: left;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {AbyssalTheme.INACTIVE_TAB};
                    color: {AbyssalTheme.TEXT_DIM};
                    border: none;
                    border-bottom: 1px solid {AbyssalTheme.BORDER};
                    border-left: 1px solid {AbyssalTheme.BORDER};
                    border-right: 1px solid {AbyssalTheme.BORDER};
                    padding: 2px 8px;
                    font-size: 11px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {AbyssalTheme.PANEL_HOVER};
                    color: {AbyssalTheme.TEXT};
                }}
            """


class TabBar(QWidget):
    tab_changed = Signal(str)
    tab_closed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.setStyleSheet(f"""
            background-color: {AbyssalTheme.INACTIVE_TAB};
            border-bottom: 1px solid {AbyssalTheme.BORDER};
        """)

        self.tabs = {}
        self.tab_order = []

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.tab_container = QWidget()
        self.tab_layout = QHBoxLayout(self.tab_container)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(0)
        self.tab_layout.addStretch()

        self.scroll.setWidget(self.tab_container)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)

    def add_tab(self, file_path: str, language: str = "text") -> None:
        if file_path in self.tabs:
            self.select_tab(file_path)
            return

        btn = TabButton(file_path, language)
        self.tabs[file_path] = btn
        self.tab_order.append(file_path)

        self.tab_layout.insertWidget(self.tab_layout.count() - 1, btn)
        self.select_tab(file_path)

    def select_tab(self, file_path: str) -> None:
        for path, btn in self.tabs.items():
            btn.set_active(path == file_path)
        self.tab_changed.emit(file_path)

    def close_tab(self, file_path: str) -> None:
        if file_path not in self.tabs:
            return

        btn = self.tabs.pop(file_path)
        if file_path in self.tab_order:
            self.tab_order.remove(file_path)
        btn.setParent(None)
        btn.deleteLater()

        self.tab_closed.emit(file_path)

        if self.tab_order:
            last_path = self.tab_order[-1]
            self.select_tab(last_path)

    def current_tab(self) -> str | None:
        for path, btn in self.tabs.items():
            if btn.isChecked():
                return path
        return None

    def update_tab(self, file_path: str, language: str) -> None:
        if file_path in self.tabs:
            self.tabs[file_path].language = language
            self.tabs[file_path]._update_text()
            active = self.tabs[file_path].isChecked()
            self.tabs[file_path].set_active(active)

    def rename_tab(self, old_path: str, new_path: str) -> None:
        if old_path not in self.tabs:
            return
        btn = self.tabs.pop(old_path)
        if old_path in self.tab_order:
            self.tab_order[self.tab_order.index(old_path)] = new_path
        btn.file_path = new_path
        btn._update_text()
        self.tabs[new_path] = btn