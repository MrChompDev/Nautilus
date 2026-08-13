import os
import shutil

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.Abyssal.src.ui.styles import AbyssalTheme

FILE_ICONS = {
    '.py': '🐍', '.js': '📜', '.jsx': '⚛️', '.ts': '📘', '.tsx': '⚛️',
    '.html': '🌐', '.htm': '🌐', '.css': '🎨', '.c': '⚙️', '.h': '⚙️',
    '.cpp': '⚙️', '.hpp': '⚙️', '.sh': '💻', '.bash': '💻', '.zsh': '💻',
    '.json': '📋', '.yaml': '📋', '.yml': '📋', '.md': '📄', '.txt': '📄',
    '.xml': '📄', '.sql': '🗄️', '.rs': '🦀', '.go': '🐹', '.java': '☕',
    '.rb': '💎', '.toml': '⚙️', '.ini': '⚙️', '.cfg': '⚙️', '.conf': '⚙️',
    '.dockerfile': '🐳', '.gitignore': '🚫', '.env': '🔐', 'default': '📄',
}

FOLDER_ICON = '📁'
FOLDER_OPEN_ICON = '📂'


def get_file_icon(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == '' and filename.lower() in FILE_ICONS:
        return FILE_ICONS[filename.lower()]
    return FILE_ICONS.get(ext, FILE_ICONS['default'])


class FileExplorerTree(QTreeWidget):
    file_selected = Signal(str)
    file_double_clicked = Signal(str)
    file_renamed = Signal(str, str)
    file_deleted = Signal(str)
    file_created = Signal(str)
    directory_changed = Signal(str)
    new_file_requested = Signal(str)
    new_folder_requested = Signal(str)
    open_in_terminal_requested = Signal(str)
    reveal_in_explorer_requested = Signal(str)
    copy_path_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setAnimated(True)
        self.setExpandsOnDoubleClick(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_double_click)
        self.itemExpanded.connect(self._on_expanded)
        self.itemCollapsed.connect(self._on_collapsed)
        
        self._root_path = None
        self._loading = set()
        self.setStyleSheet(self._style())

    def _style(self) -> str:
        return f"""
            QTreeWidget {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: none;
                outline: none;
                spacing: 1px;
            }}
            QTreeWidget::item {{
                padding: 3px 2px 3px 4px;
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
            QTreeWidget::branch {{
                background: {AbyssalTheme.PANEL};
                border: none;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                border-image: none;
                image: none;
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                border-image: none;
                image: none;
            }}
        """

    def set_root_directory(self, path: str) -> None:
        self.clear()
        if not os.path.isdir(path):
            path = os.path.expanduser("~")
        self._root_path = os.path.abspath(path)
        root_node = QTreeWidgetItem(self, [f"{FOLDER_OPEN_ICON}  {os.path.basename(self._root_path) or self._root_path}"])
        root_node.setData(0, Qt.UserRole, self._root_path)
        root_node.setData(0, Qt.UserRole + 1, True)
        self._populate_node(root_node, self._root_path)
        self.expandItem(root_node)

    def _populate_node(self, node: QTreeWidgetItem, path: str) -> None:
        if path in self._loading:
            return
        self._loading.add(path)
        try:
            entries = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        except (PermissionError, OSError):
            self._loading.discard(path)
            return

        dirs = []
        files = []
        for entry in entries:
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                if not entry.startswith('.') or entry in ('.git', '.github', '.vscode'):
                    dirs.append((entry, full))
            else:
                files.append((entry, full))

        for name, full in dirs:
            child = QTreeWidgetItem(node, [f"{FOLDER_ICON}  {name}"])
            child.setData(0, Qt.UserRole, full)
            child.setData(0, Qt.UserRole + 1, True)
            child.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)

        for name, full in files:
            icon = get_file_icon(name)
            child = QTreeWidgetItem(node, [f"{icon}  {name}"])
            child.setData(0, Qt.UserRole, full)
            child.setData(0, Qt.UserRole + 1, False)

        self._loading.discard(path)

    def _on_expanded(self, item: QTreeWidgetItem) -> None:
        path = item.data(0, Qt.UserRole)
        if path and item.data(0, Qt.UserRole + 1):
            if item.childCount() == 1 and item.child(0).text(0) == "Loading...":
                item.takeChild(0)
            if item.childCount() == 0:
                self._populate_node(item, path)
            item.setText(0, f"{FOLDER_OPEN_ICON}  {os.path.basename(path)}")

    def _on_collapsed(self, item: QTreeWidgetItem) -> None:
        path = item.data(0, Qt.UserRole)
        if path and item.data(0, Qt.UserRole + 1):
            item.setText(0, f"{FOLDER_ICON}  {os.path.basename(path)}")

    def _on_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        path = item.data(0, Qt.UserRole)
        if path and not item.data(0, Qt.UserRole + 1):
            self.file_double_clicked.emit(path)
        elif path:
            self.file_selected.emit(path)

    def _show_context_menu(self, pos: QPoint) -> None:
        item = self.itemAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER_LIGHT};
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 10px;
                spacing: 12px;
            }}
            QMenu::item:selected {{
                background-color: {AbyssalTheme.PANEL_ACTIVE};
            }}
            QMenu::separator {{
                height: 1px;
                background: {AbyssalTheme.BORDER};
                margin: 4px 12px;
            }}
        """)

        if item:
            path = item.data(0, Qt.UserRole)
            is_dir = item.data(0, Qt.UserRole + 1)

            if is_dir:
                new_file = menu.addAction("New File")
                new_file.triggered.connect(lambda: self.new_file_requested.emit(path))
                new_folder = menu.addAction("New Folder")
                new_folder.triggered.connect(lambda: self.new_folder_requested.emit(path))
                menu.addSeparator()

            open_action = menu.addAction("Open" if not is_dir else "Open Folder")
            open_action.triggered.connect(lambda: self._open_item(item))
            menu.addSeparator()

            if not is_dir:
                open_terminal = menu.addAction("Open in Terminal")
                open_terminal.triggered.connect(lambda: self.open_in_terminal_requested.emit(os.path.dirname(path)))
            else:
                open_terminal = menu.addAction("Open in Terminal")
                open_terminal.triggered.connect(lambda: self.open_in_terminal_requested.emit(path))

            reveal = menu.addAction("Reveal in File Explorer")
            reveal.triggered.connect(lambda: self.reveal_in_explorer_requested.emit(path))
            copy_path = menu.addAction("Copy Path")
            copy_path.triggered.connect(lambda: self.copy_path_requested.emit(path))
            menu.addSeparator()

            rename = menu.addAction("Rename")
            rename.triggered.connect(lambda: self._rename_item(item))
            delete = menu.addAction("Delete")
            delete.triggered.connect(lambda: self._delete_item(item))
            menu.addSeparator()

            if not is_dir:
                duplicate = menu.addAction("Duplicate")
                duplicate.triggered.connect(lambda: self._duplicate_file(item))
        else:
            new_file = menu.addAction("New File")
            new_file.triggered.connect(lambda: self.new_file_requested.emit(self._root_path))
            new_folder = menu.addAction("New Folder")
            new_folder.triggered.connect(lambda: self.new_folder_requested.emit(self._root_path))
            menu.addSeparator()
            refresh = menu.addAction("Refresh")
            refresh.triggered.connect(lambda: self.set_root_directory(self._root_path))

        menu.exec(self.mapToGlobal(pos))

    def _open_item(self, item: QTreeWidgetItem) -> None:
        path = item.data(0, Qt.UserRole)
        if path:
            if item.data(0, Qt.UserRole + 1):
                self.file_selected.emit(path)
            else:
                self.file_double_clicked.emit(path)

    def _rename_item(self, item: QTreeWidgetItem) -> None:
        path = item.data(0, Qt.UserRole)
        if not path:
            return
        old_name = os.path.basename(path)
        parent_dir = os.path.dirname(path)
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(parent_dir, new_name)
            try:
                os.rename(path, new_path)
                self.file_renamed.emit(path, new_path)
                item.setText(0, f"{get_file_icon(new_name) if not os.path.isdir(new_path) else FOLDER_ICON}  {new_name}")
                item.setData(0, Qt.UserRole, new_path)
                self._refresh_parent(item.parent() or self.invisibleRootItem())
            except OSError as e:
                QMessageBox.warning(self, "Rename Failed", str(e))

    def _delete_item(self, item: QTreeWidgetItem) -> None:
        path = item.data(0, Qt.UserRole)
        if not path:
            return
        name = os.path.basename(path)
        reply = QMessageBox.question(
            self, "Delete", f"Delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                parent = item.parent() or self.invisibleRootItem()
                parent.removeChild(item)
                self.file_deleted.emit(path)
                self._refresh_parent(parent)
            except OSError as e:
                QMessageBox.warning(self, "Delete Failed", str(e))

    def _duplicate_file(self, item: QTreeWidgetItem) -> None:
        path = item.data(0, Qt.UserRole)
        if not path or os.path.isdir(path):
            return
        base, ext = os.path.splitext(path)
        new_path = f"{base} - Copy{ext}"
        try:
            shutil.copy2(path, new_path)
            self.file_created.emit(new_path)
            parent = item.parent() or self.invisibleRootItem()
            self._refresh_parent(parent)
        except OSError as e:
            QMessageBox.warning(self, "Duplicate Failed", str(e))

    def _refresh_parent(self, parent_item) -> None:
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.data(0, Qt.UserRole + 1):
                path = child.data(0, Qt.UserRole)
                self._populate_node(child, path)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            target_item = self.itemAt(event.pos())
            target_path = self._root_path
            if target_item:
                target_path = target_item.data(0, Qt.UserRole)
                if not target_item.data(0, Qt.UserRole + 1):
                    target_path = os.path.dirname(target_path)
            
            for url in event.mimeData().urls():
                src = url.toLocalFile()
                if os.path.exists(src):
                    dst = os.path.join(target_path, os.path.basename(src))
                    try:
                        if os.path.isdir(src):
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)
                        self.file_created.emit(dst)
                        self._refresh_parent(target_item or self.invisibleRootItem())
                    except OSError as e:
                        QMessageBox.warning(self, "Copy Failed", str(e))
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class FileExplorerPanel(QWidget):
    file_selected = Signal(str)
    file_double_clicked = Signal(str)
    file_renamed = Signal(str, str)
    file_deleted = Signal(str)
    file_created = Signal(str)
    directory_changed = Signal(str)
    open_in_terminal_requested = Signal(str)
    reveal_in_explorer_requested = Signal(str)
    copy_path_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AbyssalTheme.PANEL};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tree must exist before the header (collapse button connects to it)
        self.tree = FileExplorerTree()

        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            border-bottom: 1px solid {AbyssalTheme.BORDER};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        
        title = QLabel("EXPLORER")
        title.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.refresh_btn = self._create_button("⟳", "Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(self.refresh_btn)
        
        self.collapse_btn = self._create_button("▲", "Collapse All")
        self.collapse_btn.clicked.connect(self.tree.collapseAll)
        header_layout.addWidget(self.collapse_btn)
        
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
            QLineEdit:focus {{ border-color: {AbyssalTheme.ACCENT}; }}
        """)
        search.textChanged.connect(self._filter_files)
        layout.addWidget(search)
        self.search = search

        self.tree.file_selected.connect(self.file_selected.emit)
        self.tree.file_double_clicked.connect(self.file_double_clicked.emit)
        self.tree.file_renamed.connect(self.file_renamed.emit)
        self.tree.file_deleted.connect(self.file_deleted.emit)
        self.tree.file_created.connect(self.file_created.emit)
        self.tree.new_file_requested.connect(self._on_new_file)
        self.tree.new_folder_requested.connect(self._on_new_folder)
        self.tree.open_in_terminal_requested.connect(self.open_in_terminal_requested.emit)
        self.tree.reveal_in_explorer_requested.connect(self.reveal_in_explorer_requested.emit)
        self.tree.copy_path_requested.connect(self.copy_path_requested.emit)
        layout.addWidget(self.tree)

    def _create_button(self, text: str, tooltip: str) -> QWidget:
        from PySide6.QtWidgets import QToolButton
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(24, 24)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {AbyssalTheme.TEXT_DIM};
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }}
            QToolButton:hover {{
                background-color: {AbyssalTheme.PANEL_HOVER};
                color: {AbyssalTheme.TEXT};
            }}
        """)
        return btn

    def _filter_files(self, text: str) -> None:
        text = text.lower()
        def filter_item(item):
            if item.childCount() == 0:
                item.setHidden(text not in item.text(0).lower())
            else:
                visible = False
                for i in range(item.childCount()):
                    if filter_item(item.child(i)):
                        visible = True
                item.setHidden(not visible)
                return visible
        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))

    def _on_new_file(self, directory: str) -> None:
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name:
            path = os.path.join(directory, name)
            try:
                open(path, 'w').close()
                self.tree.file_created.emit(path)
                self._refresh_parent_dir(directory)
            except OSError as e:
                QMessageBox.warning(self, "Create Failed", str(e))

    def _on_new_folder(self, directory: str) -> None:
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            path = os.path.join(directory, name)
            try:
                os.makedirs(path, exist_ok=True)
                self.tree.file_created.emit(path)
                self._refresh_parent_dir(directory)
            except OSError as e:
                QMessageBox.warning(self, "Create Failed", str(e))

    def _refresh_parent_dir(self, path: str) -> None:
        def find_and_refresh(item):
            if item.data(0, Qt.UserRole) == path:
                self.tree._refresh_parent(item)
                return True
            for i in range(item.childCount()):
                if find_and_refresh(item.child(i)):
                    return True
            return False
        
        for i in range(self.tree.topLevelItemCount()):
            if find_and_refresh(self.tree.topLevelItem(i)):
                break

    def set_root_directory(self, path: str) -> None:
        self.tree.set_root_directory(path)

    def refresh(self) -> None:
        self.tree.set_root_directory(self.tree._root_path)

    def collapse_all(self) -> None:
        self.tree.collapseAll()