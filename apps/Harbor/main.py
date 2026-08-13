#!/usr/bin/env python3
"""
Harbor — Nautilus Keyboard-First File Manager
Dual-pane layout with Vim-style shortcuts, inline previews, and archive support.
"""

import mimetypes
import os
import shutil
import sys
import tarfile
import zipfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QPalette,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from core.theme import (
        COLORS,
        FONTS,
        SPACING,
        create_nautilus_palette,
        get_global_stylesheet,
    )
except ImportError:
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
        "seafoam_deep": "#004D40", "coral": "#FF7F50", "amber": "#FFA502",
        "emerald": "#00C853", "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8",
        "text_muted": "#506070", "border": "#152D44", "surface_hover": "#132A40",
        "surface_selected": "#1A3352", "scrollbar_bg": "#050D14", "scrollbar_handle": "#1A3352",
        "scrollbar_hover": "#254565",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11, "size_md": 12, "size_lg": 13, "size_xl": 14, "size_xxl": 16}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "xxl": 24}
    def get_global_stylesheet(): return ""
    def create_nautilus_palette(): return QPalette()


# ═══════════════════════════════════════════════════════════════
#  FILE PANE
# ═══════════════════════════════════════════════════════════════

class FilePane(QWidget):
    """A single file navigation pane with path bar and tree view."""

    path_changed = None  # Signal placeholder - connected externally

    def __init__(self, pane_id: str, parent=None):
        super().__init__(parent)
        self._pane_id = pane_id
        self._current_path = os.path.expanduser("~")
        self._history = []
        self._history_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Path bar ──
        path_bar = QHBoxLayout()
        path_bar.setSpacing(SPACING["xs"])

        self._path_label = QLabel(pane_id.upper())
        self._path_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['seafoam']};
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_xs']}px;
                font-weight: bold;
                padding: 2px 6px;
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['void_black']};
            }}
        """)
        path_bar.addWidget(self._path_label)

        self._path_input = QLineEdit()
        self._path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['deep_navy']};
                color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 3px 8px;
            }}
        """)
        self._path_input.returnPressed.connect(self._on_path_entered)
        path_bar.addWidget(self._path_input, 1)

        layout.addLayout(path_bar)

        # ── Tree View ──
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Name", "Size", "Modified"])
        self._tree.setColumnWidth(0, 260)
        self._tree.setColumnWidth(1, 90)
        self._tree.setColumnWidth(2, 130)
        self._tree.setRootIsDecorated(True)
        self._tree.setAlternatingRowColors(False)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS['slate_navy']};
                color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
            }}
            QTreeWidget::item {{ padding: 2px 4px; border: none; }}
            QTreeWidget::item:hover {{ background-color: {COLORS['surface_hover']}; }}
            QTreeWidget::item:selected {{ background-color: {COLORS['surface_selected']}; color: {COLORS['seafoam']}; }}
            QHeaderView::section {{
                background-color: {COLORS['void_black']};
                color: {COLORS['seafoam']};
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_xs']}px;
                padding: 3px 6px;
                border: none;
                border-right: 1px solid {COLORS['border']};
                border-bottom: 2px solid {COLORS['border']};
            }}
        """)
        self._tree.itemDoubleClicked.connect(self._on_item_double_click)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._tree, 1)

        # ── Status ──
        self._status = QLabel("")
        self._status.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            padding: 2px 6px;
            border-top: 1px solid {COLORS['border']};
            background-color: {COLORS['deep_navy']};
        """)
        layout.addWidget(self._status)

        self._refresh()

    def _navigate_to(self, path: str):
        """Navigate to a directory path."""
        path = os.path.abspath(os.path.expanduser(path))
        if os.path.isdir(path):
            self._current_path = path
            self._path_input.setText(path)
            self._refresh()
            # Update history
            if self._history_index < len(self._history) - 1:
                self._history = self._history[:self._history_index + 1]
            self._history.append(path)
            self._history_index = len(self._history) - 1

    def _on_path_entered(self):
        self._navigate_to(self._path_input.text())

    def _on_item_double_click(self, item: QTreeWidgetItem, column: int):
        path = item.data(0, Qt.UserRole)
        if path and os.path.isdir(path):
            self._navigate_to(path)

    def _refresh(self):
        """Refresh the tree view for current path."""
        self._tree.clear()
        self._path_input.setText(self._current_path)

        try:
            entries = sorted(os.scandir(self._current_path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            self._status.setText("⚠ Permission denied")
            return

        dir_count = 0
        file_count = 0

        for entry in entries:
            try:
                stat = entry.stat()
                size_str = ""
                if entry.is_file():
                    size_str = self._fmt_size(stat.st_size)
                    file_count += 1
                elif entry.is_dir():
                    dir_count += 1

                import datetime
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                item = QTreeWidgetItem([entry.name, size_str, mtime])
                item.setData(0, Qt.UserRole, entry.path)

                # Icon / color by type
                if entry.is_dir():
                    item.setForeground(0, QColor(COLORS["seafoam"]))
                elif entry.name.endswith((".py", ".js", ".ts", ".cpp", ".c", ".h", ".rs", ".go", ".java")):
                    item.setForeground(0, QColor(COLORS["amber"]))
                elif entry.name.endswith((".zip", ".tar", ".gz", ".7z", ".rar")):
                    item.setForeground(0, QColor(COLORS["coral"]))
                elif entry.name.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")):
                    item.setForeground(0, QColor("#4AA8FF"))
                elif entry.name.startswith("."):
                    item.setForeground(0, QColor(COLORS["text_muted"]))

                # Lazy-load indicator for directories
                if entry.is_dir():
                    # Check if non-empty
                    try:
                        has_children = any(True for _ in os.scandir(entry.path))
                        if has_children:
                            placeholder = QTreeWidgetItem(["(loading...)", "", ""])
                            placeholder.setForeground(0, QColor(COLORS["text_muted"]))
                            item.addChild(placeholder)
                    except Exception:
                        pass

                self._tree.addTopLevelItem(item)

            except Exception:
                pass

        self._status.setText(f"  {dir_count} dirs  |  {file_count} files  |  {self._current_path}")

    def _on_context_menu(self, pos: QPoint):
        items = self._tree.selectedItems()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {COLORS['slate_navy']}; color: {COLORS['hd_white']}; border: 1px solid {COLORS['border']}; }}
            QMenu::item:selected {{ background-color: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']}; }}
        """)

        if items:
            paths = [item.data(0, Qt.UserRole) for item in items if item.data(0, Qt.UserRole)]
            if paths:
                delete_action = menu.addAction("🗑  Delete")
                delete_action.triggered.connect(lambda: self._delete_files(paths))

                rename_action = menu.addAction("✏  Rename")
                rename_action.triggered.connect(lambda: self._rename_file(paths[0]))

                menu.addSeparator()

                copy_action = menu.addAction("📋  Copy Path")
                copy_action.triggered.connect(lambda: self._copy_paths(paths))

                menu.addSeparator()

                if len(paths) == 1 and os.path.isfile(paths[0]):
                    compress_action = menu.addAction("📦  Compress (.zip)")
                    compress_action.triggered.connect(lambda: self._compress_file(paths[0]))

                    compress_tar = menu.addAction("📦  Compress (.tar.gz)")
                    compress_tar.triggered.connect(lambda: self._compress_tar(paths[0]))

        new_folder = menu.addAction("📁  New Folder")
        new_folder.triggered.connect(self._new_folder)

        new_file = menu.addAction("📄  New File")
        new_file.triggered.connect(self._new_file)

        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _delete_files(self, paths: list):
        msg = f"Delete {len(paths)} item(s)?\n\n" + "\n".join(p[:60] for p in paths[:5])
        reply = QMessageBox.question(self, "Delete", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for p in paths:
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p)
                    else:
                        os.remove(p)
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
            self._refresh()

    def _rename_file(self, path: str):
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=os.path.basename(path))
        if ok and name:
            new_path = os.path.join(os.path.dirname(path), name)
            try:
                os.rename(path, new_path)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _copy_paths(self, paths: list):
        QApplication.clipboard().setText("\n".join(paths))

    def _compress_file(self, path: str):
        dest = path + ".zip"
        try:
            with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for f in files:
                            fp = os.path.join(root, f)
                            zf.write(fp, os.path.relpath(fp, os.path.dirname(path)))
                else:
                    zf.write(path, os.path.basename(path))
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _compress_tar(self, path: str):
        dest = path + ".tar.gz"
        try:
            with tarfile.open(dest, "w:gz") as tf:
                tf.add(path, arcname=os.path.basename(path))
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _new_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            p = os.path.join(self._current_path, name)
            try:
                os.makedirs(p, exist_ok=True)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _new_file(self):
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name:
            p = os.path.join(self._current_path, name)
            try:
                with open(p, "w") as f:
                    f.write("")
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def go_back(self):
        if self._history_index > 0:
            self._history_index -= 1
            self._current_path = self._history[self._history_index]
            self._path_input.setText(self._current_path)
            self._refresh()

    def go_forward(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._current_path = self._history[self._history_index]
            self._path_input.setText(self._current_path)
            self._refresh()

    def go_up(self):
        parent = os.path.dirname(self._current_path)
        if parent != self._current_path:
            self._navigate_to(parent)

    def get_current_path(self) -> str:
        return self._current_path

    def get_selected_paths(self) -> list:
        items = self._tree.selectedItems()
        return [item.data(0, Qt.UserRole) for item in items if item.data(0, Qt.UserRole)]

    @staticmethod
    def _fmt_size(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


# ═══════════════════════════════════════════════════════════════
#  FILE PREVIEW PANEL
# ═══════════════════════════════════════════════════════════════

class FilePreview(QWidget):
    """Inline preview for selected files — text, image, code, hex."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._title = QLabel("PREVIEW")
        self._title.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px; font-weight: bold; letter-spacing: 1px;
            padding: 4px 8px; border-bottom: 1px solid {COLORS['border']};
            background-color: {COLORS['void_black']};
        """)
        layout.addWidget(self._title)

        self._content = QTextEdit()
        self._content.setReadOnly(True)
        self._content.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['terminal_bg']};
                color: {COLORS['hd_white']};
                border: none;
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
            }}
        """)
        layout.addWidget(self._content, 1)

    def preview(self, path: str):
        """Preview a file by path."""
        if not path or not os.path.isfile(path):
            self._title.setText("PREVIEW")
            self._content.clear()
            return

        self._title.setText(f"PREVIEW  //  {os.path.basename(path)}")
        size = os.path.getsize(path)

        # Text files
        text_exts = {".py", ".js", ".ts", ".cpp", ".c", ".h", ".rs", ".go", ".java",
                     ".txt", ".md", ".json", ".xml", ".html", ".css", ".yaml", ".yml",
                     ".toml", ".ini", ".cfg", ".sh", ".bash", ".zsh", ".fish",
                     ".rb", ".php", ".sql", ".r", ".m", ".swift", ".kt", ".scala",
                     ".lua", ".vim", ".tex", ".gradle", ".properties", ".env", ".gitignore"}
        ext = os.path.splitext(path)[1].lower()

        if ext in text_exts and size < 1024 * 1024:  # 1MB limit
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    content = f.read(50000)
                self._content.setPlainText(content)
                return
            except Exception:
                pass

        # Binary / unknown
        self._content.setPlainText(f"[Binary file — {size:,} bytes]\n\n"
                                   f"Path: {path}\n"
                                   f"Type: {mimetypes.guess_type(path)[0] or 'unknown'}")


# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class HarborWindow(QMainWindow):
    """Harbor — Nautilus Keyboard-First File Manager."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Harbor — File Manager")
        self.setMinimumSize(1000, 600)
        self.resize(1300, 750)

        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        main_layout.setSpacing(SPACING["sm"])

        # Title bar
        title = QLabel("📁  HARBOR  //  Keyboard-First File Manager")
        title.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_lg']}px; font-weight: bold; letter-spacing: 2px;
            padding-bottom: 4px; border-bottom: 1px solid {COLORS['border']};
        """)
        main_layout.addWidget(title)

        # Navigation toolbar
        nav = QHBoxLayout()
        nav.setSpacing(SPACING["xs"])

        for label, slot_name in [("◀", "go_back"), ("▶", "go_forward"), ("▲", "go_up"), ("↻", "refresh")]:
            btn = QPushButton(label)
            btn.setFixedSize(30, 26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['slate_navy']};
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border']};
                    font-size: 14px;
                }}
                QPushButton:hover {{ color: {COLORS['seafoam']}; border-color: {COLORS['seafoam_dim']}; }}
            """)
            nav.addWidget(btn)

        nav.addStretch()

        # Shortcut hints
        hints = QLabel("j/k ↑↓:nav  Enter:open  Backspace:up  /:search  h/l:switch  Space:preview  Del:delete  F5:copy  F6:move  F7:mkdir  F8:delete")
        hints.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
        nav.addWidget(hints)

        main_layout.addLayout(nav)

        # Main splitter: left pane | right pane | preview
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {COLORS['border']}; width: 2px; }}")

        self._left_pane = FilePane("LEFT")
        self._right_pane = FilePane("RIGHT")
        self._preview = FilePreview()

        splitter.addWidget(self._left_pane)
        splitter.addWidget(self._right_pane)
        splitter.addWidget(self._preview)
        splitter.setSizes([400, 400, 300])

        main_layout.addWidget(splitter, 1)

        # Connect selection in left pane to preview
        self._left_pane._tree.itemSelectionChanged.connect(self._on_left_selection)
        self._right_pane._tree.itemSelectionChanged.connect(self._on_right_selection)

        # Active pane tracking
        self._active_pane = self._left_pane
        self._left_pane._tree.setFocus()

        # Track active pane via event filter
        self._left_pane._tree.installEventFilter(self)
        self._right_pane._tree.installEventFilter(self)

        # Connect nav buttons - they're the first 4 widgets in the layout
        # Store refs in nav layout for connection
        nav_buttons = []
        for i in range(nav.count()):
            item = nav.itemAt(i)
            if item and item.widget():
                nav_buttons.append(item.widget())

        if len(nav_buttons) >= 4:
            nav_buttons[0].clicked.connect(lambda: self._active_pane.go_back())
            nav_buttons[1].clicked.connect(lambda: self._active_pane.go_forward())
            nav_buttons[2].clicked.connect(lambda: self._active_pane.go_up())
            nav_buttons[3].clicked.connect(lambda: self._active_pane._refresh())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            if obj is self._left_pane._tree:
                self._active_pane = self._left_pane
            elif obj is self._right_pane._tree:
                self._active_pane = self._right_pane
        return super().eventFilter(obj, event)

    def _set_active(self, pane):
        self._active_pane = pane

    def _setup_shortcuts(self):
        """Vim-style keyboard shortcuts."""
        # Navigation
        QShortcut(QKeySequence("j"), self).activated.connect(lambda: self._move_cursor(1))
        QShortcut(QKeySequence("k"), self).activated.connect(lambda: self._move_cursor(-1))
        QShortcut(QKeySequence("h"), self).activated.connect(lambda: self._switch_to_left())
        QShortcut(QKeySequence("l"), self).activated.connect(lambda: self._switch_to_right())
        QShortcut(QKeySequence("Return"), self).activated.connect(self._open_selected)
        QShortcut(QKeySequence("Backspace"), self).activated.connect(lambda: self._active_pane.go_up())
        QShortcut(QKeySequence("Alt+Left"), self).activated.connect(lambda: self._active_pane.go_back())
        QShortcut(QKeySequence("Alt+Right"), self).activated.connect(lambda: self._active_pane.go_forward())

        # Actions
        QShortcut(QKeySequence("Delete"), self).activated.connect(self._delete_current)
        QShortcut(QKeySequence("F5"), self).activated.connect(self._copy_files)
        QShortcut(QKeySequence("F6"), self).activated.connect(self._move_files)
        QShortcut(QKeySequence("F7"), self).activated.connect(self._active_pane._new_folder)
        QShortcut(QKeySequence("Space"), self).activated.connect(self._preview_current)

        # Search
        QShortcut(QKeySequence("/"), self).activated.connect(self._focus_search)

    def _move_cursor(self, delta: int):
        tree = self._active_pane._tree
        current = tree.currentItem()
        if current:
            idx = tree.indexOfTopLevelItem(current)
            new_idx = max(0, min(tree.topLevelItemCount() - 1, idx + delta))
            tree.setCurrentItem(tree.topLevelItem(new_idx))
        elif tree.topLevelItemCount() > 0:
            tree.setCurrentItem(tree.topLevelItem(0))

    def _switch_to_left(self):
        self._active_pane = self._left_pane
        self._left_pane._tree.setFocus()

    def _switch_to_right(self):
        self._active_pane = self._right_pane
        self._right_pane._tree.setFocus()

    def _open_selected(self):
        items = self._active_pane._tree.selectedItems()
        if items:
            path = items[0].data(0, Qt.UserRole)
            if path and os.path.isdir(path):
                self._active_pane._navigate_to(path)

    def _delete_current(self):
        paths = self._active_pane.get_selected_paths()
        if paths:
            self._active_pane._delete_files(paths)

    def _copy_files(self):
        src_paths = self._left_pane.get_selected_paths()
        dest_dir = self._right_pane.get_current_path()
        if src_paths and dest_dir:
            for src in src_paths:
                dest = os.path.join(dest_dir, os.path.basename(src))
                try:
                    if os.path.isdir(src):
                        shutil.copytree(src, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dest)
                except Exception as e:
                    QMessageBox.critical(self, "Copy Error", str(e))
            self._right_pane._refresh()

    def _move_files(self):
        src_paths = self._left_pane.get_selected_paths()
        dest_dir = self._right_pane.get_current_path()
        if src_paths and dest_dir:
            for src in src_paths:
                dest = os.path.join(dest_dir, os.path.basename(src))
                try:
                    shutil.move(src, dest)
                except Exception as e:
                    QMessageBox.critical(self, "Move Error", str(e))
            self._left_pane._refresh()
            self._right_pane._refresh()

    def _preview_current(self):
        items = self._active_pane._tree.selectedItems()
        if items:
            path = items[0].data(0, Qt.UserRole)
            if path:
                self._preview.preview(path)

    def _focus_search(self):
        self._active_pane._path_input.setFocus()
        self._active_pane._path_input.selectAll()

    def _on_left_selection(self):
        items = self._left_pane._tree.selectedItems()
        if items:
            path = items[0].data(0, Qt.UserRole)
            if path and os.path.isfile(path):
                self._preview.preview(path)

    def _on_right_selection(self):
        items = self._right_pane._tree.selectedItems()
        if items:
            path = items[0].data(0, Qt.UserRole)
            if path and os.path.isfile(path):
                self._preview.preview(path)


# ═══════════════════════════════════════════════════════════════

def main():
    try:
        from core.logger import get_logger
        log = get_logger("APP")
        log.info("Harbor File Manager starting")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Harbor")
    app.setOrganizationName("Nautilus")

    try:
        from core.icons import get_logo
        app.setWindowIcon(get_logo("harbor"))
    except Exception:
        pass

    app.setPalette(create_nautilus_palette())
    app.setStyleSheet(get_global_stylesheet())

    font = QFont()
    font.setFamilies([FONTS["ui"], FONTS["mono"], "Consolas"])
    font.setPointSize(FONTS["size_md"])
    app.setFont(font)

    window = HarborWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
