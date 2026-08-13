from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QStackedWidget,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from apps.Abyssal.src.ui.styles import AbyssalTheme

FILE_EXTENSIONS = {
    '.py': '\U0001f40d', '.js': 'JS', '.jsx': 'JS',
    '.ts': 'TS', '.tsx': 'TS', '.html': '\U0001f310', '.htm': '\U0001f310',
    '.css': '\U0001f3a8', '.c': 'C', '.h': 'C',
    '.cpp': 'C++', '.hpp': 'C++', '.sh': '\U0001f680', '.bash': '\U0001f680',
    '.json': '{}', '.yaml': 'Y', '.yml': 'Y',
    '.md': '\U0001f4c4', '.txt': '\U0001f4c4',
    '.xml': '</>', '.sql': '\u25C6', '.rs': 'R',
    '.go': 'Go', '.java': 'J', '.rb': 'Ru', '.toml': 'T', '.ini': 'I',
}


class FileExplorerPanel(QWidget):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AbyssalTheme.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  EXPLORER")
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            font-size: 11px;
            font-weight: bold;
            border-bottom: 1px solid {AbyssalTheme.BORDER};
            padding-top: 8px;
            spacing: 4px;
        """)
        layout.addWidget(header)

        search = QLineEdit()
        search.setPlaceholderText("Filter files...")
        search.setFixedHeight(28)
        search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                margin: 4px 8px;
            }}
            QLineEdit:focus {{
                border-color: {AbyssalTheme.ACCENT};
            }}
        """)
        layout.addWidget(search)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setAnimated(True)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: none;
                outline: none;
                spacing: 1px;
            }}
            QTreeWidget::item {{
                padding: 3px 4px 3px 2px;
                border: none;
                min-height: 22px;
            }}
            QTreeWidget::item:hover {{
                background-color: {AbyssalTheme.PANEL_HOVER};
            }}
            QTreeWidget::item:selected {{
                background-color: {AbyssalTheme.SELECTION};
                color: {AbyssalTheme.TEXT};
                border: none;
            }}
            QTreeWidget::branch {{
                background: {AbyssalTheme.PANEL};
                border: none;
            }}
        """)
        layout.addWidget(self.tree)

    def _on_click(self, index) -> None:
        pass

    def set_root_directory(self, path: str) -> None:
        pass


class SearchPanel(QWidget):
    search_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AbyssalTheme.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        header = QLabel("  SEARCH")
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            font-size: 11px;
            font-weight: bold;
            border-bottom: 1px solid {AbyssalTheme.BORDER};
            padding-top: 8px;
        """)
        layout.addWidget(header)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.returnPressed.connect(self._do_search)
        layout.addWidget(self.search_input)

        self.results_label = QLabel("")
        self.results_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; padding: 4px 8px; font-size: 10px;")
        layout.addWidget(self.results_label)

        self.result_tree = QTreeWidget()
        self.result_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 2px 4px;
                border: none;
                min-height: 20px;
            }}
            QTreeWidget::item:hover {{
                background-color: {AbyssalTheme.PANEL_HOVER};
            }}
            QTreeWidget::item:selected {{
                background-color: {AbyssalTheme.SELECTION};
                color: {AbyssalTheme.TEXT};
            }}
        """)
        layout.addWidget(self.result_tree)

        layout.addStretch()

    def _do_search(self) -> None:
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)


class ExtensionsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AbyssalTheme.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("  EXTENSIONS")
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            font-size: 11px;
            font-weight: bold;
            border-bottom: 1px solid {AbyssalTheme.BORDER};
            padding-top: 8px;
        """)
        layout.addWidget(header)

        msg = QLabel("  No extensions installed.\n\n  Abyssal ships with\n  built-in syntax\n  highlighting for:\n\n  Python, JS, TS,\n  C/C++, HTML, CSS,\n  Shell, JSON,\n  YAML, Markdown")
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; padding: 16px; font-size: 10px;")
        layout.addWidget(msg)

        layout.addStretch()


class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AbyssalTheme.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("  SETTINGS")
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            font-size: 11px;
            font-weight: bold;
            border-bottom: 1px solid {AbyssalTheme.BORDER};
            padding-top: 8px;
        """)
        layout.addWidget(header)

        info = QLabel(
            "  Abyssal Editor v2.0\n\n"
            "  Framework: PyQt5\n\n"
            "  Theme: Navy/Seafoam\n"
            "  Font: JetBrains Mono\n\n"
            "  Keyboard Shortcuts:\n"
            "  Ctrl+S       Save\n"
            "  Ctrl+Shift+P Command Palette\n"
            "  Ctrl+F       Find\n"
            "  Ctrl+H       Find & Replace\n"
            "  F5           Run File\n"
            "  Ctrl+R       Run File\n"
            "  Ctrl+P       Quick Open\n"
            "  Ctrl+B       Toggle Sidebar\n"
            "  Ctrl+`       Toggle Terminal\n"
            "  Ctrl+Shift+E Explorer\n"
            "  Ctrl+Shift+F Search"
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; padding: 16px; font-size: 10px;")
        layout.addWidget(info)

        layout.addStretch()


class Sidebar(QWidget):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(64)
        self.setMaximumWidth(500)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AbyssalTheme.PANEL};
                border-right: 1px solid {AbyssalTheme.BORDER};
            }}
        """)

        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        self.explorer = FileExplorerPanel()
        self.explorer.file_selected.connect(self.file_selected.emit)
        self.search = SearchPanel()
        self.extensions = ExtensionsPanel()
        self.settings = SettingsPanel()

        self.stack.addWidget(self.explorer)
        self.stack.addWidget(self.search)
        self.stack.addWidget(self.extensions)
        self.stack.addWidget(self.settings)

        self.panel_map = {
            "explorer": 0,
            "search": 1,
            "extensions": 2,
            "settings": 3,
        }

    def show_panel(self, name: str) -> None:
        if name in self.panel_map:
            self.stack.setCurrentIndex(self.panel_map[name])
            self.show()