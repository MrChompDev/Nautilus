from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.Abyssal.src.ui.styles import AbyssalTheme


class CommandPalette(QWidget):
    command_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setFixedWidth(580)
        self.setFixedHeight(380)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AbyssalTheme.PANEL};
                border: 1px solid {AbyssalTheme.BORDER_LIGHT};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type a command or search...")
        self.search_bar.setFixedHeight(36)
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: none;
                border-bottom: 1px solid {AbyssalTheme.BORDER};
                padding: 0 14px;
                font-size: 13px;
                border-radius: 6px 6px 0 0;
            }}
            QLineEdit:focus {{
                border-bottom-color: {AbyssalTheme.ACCENT};
            }}
        """)
        self.search_bar.textChanged.connect(self._filter)
        layout.addWidget(self.search_bar)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: none;
                outline: none;
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 7px 14px;
                border: none;
                spacing: 8px;
            }}
            QListWidget::item:selected {{
                background-color: {AbyssalTheme.SELECTION};
                color: {AbyssalTheme.TEXT};
            }}
            QListWidget::item:hover {{
                background-color: {AbyssalTheme.PANEL_HOVER};
            }}
            QListWidget::item:first-child {{
                border-top: 1px solid {AbyssalTheme.BORDER_LIGHT};
            }}
        """)
        self.list_widget.keyPressEvent = self._list_key_press
        self.list_widget.itemDoubleClicked.connect(self._execute)
        layout.addWidget(self.list_widget)

        self._commands = []
        self._filtered = []

    def add_command(self, name: str, shortcut: str = "") -> None:
        display = f"{name}    {shortcut}" if shortcut else name
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, name)
        item.setFont(QFont("Segoe UI", 11))
        self._commands.append((name, display, item))
        self.list_widget.addItem(item)

    def showEvent(self, event):
        super().showEvent(event)
        self.search_bar.clear()
        self._filter("")
        self.search_bar.setFocus()
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter(self, text: str) -> None:
        text = text.lower()
        for name, display, item in self._commands:
            item.setHidden(text not in display.lower())
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _execute(self, item=None) -> None:
        if item is None:
            item = self.list_widget.currentItem()
        if item:
            self.command_selected.emit(item.data(Qt.UserRole))
            self.hide()

    def _list_key_press(self, event) -> None:
        if event.key() == Qt.Key_Return:
            self._execute()
        elif event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key_Up:
            row = self.list_widget.currentRow()
            if row > 0:
                self.list_widget.setCurrentRow(row - 1)
        elif event.key() == Qt.Key_Down:
            row = self.list_widget.currentRow()
            if row < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(row + 1)
        else:
            super(QListWidget, self.list_widget).keyPressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._execute()
        elif event.key() == Qt.Key_Down:
            self.list_widget.setFocus()
        else:
            super().keyPressEvent(event)