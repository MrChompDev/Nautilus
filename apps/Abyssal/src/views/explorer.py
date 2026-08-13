import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from apps.Abyssal.src.ui.styles import AbyssalTheme


class ExplorerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AbyssalTheme.PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  EXPLORER")
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL};
            color: {AbyssalTheme.TEXT_DIM};
            font-size: 11px;
            font-weight: bold;
            border-bottom: 1px solid {AbyssalTheme.BORDER};
            padding-top: 8px;
        """)
        layout.addWidget(header)

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
            }}
            QTreeWidget::item {{
                padding: 3px 0;
                border: none;
                min-height: 22px;
            }}
            QTreeWidget::item:hover {{
                background-color: {AbyssalTheme.PANEL_HOVER};
            }}
            QTreeWidget::item:selected {{
                background-color: {AbyssalTheme.SELECTION};
                color: {AbyssalTheme.TEXT};
            }}
        """)
        layout.addWidget(self.tree)

    def set_root_directory(self, path: str) -> None:
        self.tree.clear()
        if not os.path.isdir(path):
            path = os.path.expanduser("~")
        root_node = QTreeWidgetItem(self.tree, [os.path.basename(path) or path])
        root_node.setData(0, Qt.UserRole, path)
        self._populate_node(root_node, path)
        self.tree.expandAll()

    def _populate_node(self, node: QTreeWidgetItem, path: str) -> None:
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return

        dirs = []
        files = []
        for entry in entries:
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                dirs.append((entry, full))
            else:
                ext = os.path.splitext(entry)[1].lower()
                if ext in {'.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.htm',
                           '.css', '.c', '.h', '.cpp', '.hpp', '.sh', '.bash',
                           '.json', '.yaml', '.yml', '.md', '.xml', '.sql',
                           '.rs', '.go', '.java', '.rb', '.toml', '.ini', '.txt'}:
                    files.append((entry, full))

        for name, full in dirs:
            child = QTreeWidgetItem(node, [name])
            child.setData(0, Qt.UserRole, full)
            self._populate_node(child, full)

        for name, full in files:
            child = QTreeWidgetItem(node, [name])
            child.setData(0, Qt.UserRole, full)