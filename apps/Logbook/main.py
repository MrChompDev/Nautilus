#!/usr/bin/env python3
"""
Logbook — Nautilus Markdown Notes
Keyboard-first notes app: live markdown preview, instant search, auto-save,
and a naval logbook archive. Stores notes as plain .md files in ~/Documents/Logbook.
"""

import os
import re
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from core.logger import get_logger
    from core.theme import (
        COLORS,
        FONTS,
        SPACING,
        create_nautilus_palette,
        get_global_stylesheet,
        glass_bg,
        glass_bg_dark,
        glass_edge,
        glass_sheen,
    )
except ImportError:
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
        "seafoam_deep": "#004D40", "coral": "#FF7F50", "amber": "#FFA502",
        "emerald": "#00C853", "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8",
        "text_muted": "#506070", "border": "#152D44", "surface_hover": "#132A40",
        "surface_selected": "#1A3352", "scrollbar_bg": "#050D14", "scrollbar_handle": "#1A3352",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11, "size_md": 12, "size_lg": 13, "size_xl": 14}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "xxl": 24}

    def get_global_stylesheet(): return ""
    def create_nautilus_palette(): return QPalette()

    def hex_to_rgba(h, a=255):
        v = h.lstrip("#")
        return f"rgba({int(v[0:2],16)},{int(v[2:4],16)},{int(v[4:6],16)},{a})"
    def glass_bg(a=180): return hex_to_rgba(COLORS["slate_navy"], a)
    def glass_bg_dark(a=140): return hex_to_rgba(COLORS["deep_navy"], a)
    def glass_edge(a=48): return hex_to_rgba(COLORS["seafoam"], a)
    def glass_sheen(): return "rgba(238, 244, 248, 26)"

APP_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Logbook")
FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class Note:
    """A single markdown note backed by a .md file."""
    def __init__(self, path: str):
        self.path = path

    @property
    def title(self) -> str:
        base = os.path.splitext(os.path.basename(self.path))[0]
        return base or "Untitled"

    @property
    def mtime(self) -> float:
        try:
            return os.path.getmtime(self.path)
        except OSError:
            return 0

    def read(self) -> str:
        try:
            with open(self.path, encoding="utf-8") as f:
                return f.read()
        except (OSError, UnicodeDecodeError):
            return ""

    def write(self, text: str) -> bool:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(text)
            return True
        except OSError:
            return False

    @staticmethod
    def safe_filename(title: str) -> str:
        cleaned = FILENAME_CHARS.sub("_", title.strip())
        return cleaned or "untitled"


def _render_markdown(text: str) -> str:
    """Render a safe subset of markdown to HTML for preview."""
    import html
    out = []
    in_list = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("")
            continue
        if stripped.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{html.escape(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h1>{html.escape(stripped[2:])}</h1>")
        elif stripped.startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{html.escape(stripped[2:])}</li>")
        elif re.match(r"^\s*[-*_]{3,}\s*$", stripped):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<hr/>")
        elif stripped.startswith("```"):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<pre class='code'>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{html.escape(stripped)}</p>")
    if in_list:
        out.append("</ul>")
    body = "\n".join(out)
    return (
        "<style>"
        "body{color:" + COLORS["hd_white"] + ";font-family:'JetBrains Mono',Consolas,monospace;font-size:14px;line-height:1.7;}"
        "h1,h2,h3{color:" + COLORS["seafoam"] + ";margin-top:22px;}"
        "h1{font-size:24px;border-bottom:1px solid " + glass_edge() + ";padding-bottom:6px;}"
        "li{color:" + COLORS["text_secondary"] + ";}"
        "hr{border:0;border-top:1px solid " + glass_edge() + ";}"
        "pre.code{background:" + glass_bg_dark(160) + ";padding:12px;color:" + COLORS["amber"] + ";border:1px solid "
        + glass_edge() + ";overflow:auto;}"
        "p{color:" + COLORS["text_secondary"] + ";}"
        "</style><body>" + body + "</body>"
    )


class LogbookWindow(QMainWindow):
    """Logbook — markdown notes with live preview, search, and auto-save."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logbook — Notes")
        self.resize(1080, 720)
        self._notes: dict[str, Note] = {}
        self._current_path: str | None = None
        self._dirty = False
        self._saving = False

        self._build_ui()
        self._load_notes()
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._flush_save)
        self._auto_save_timer.start(2000)

        if self._notes:
            self._notes_list.setCurrentRow(0)
            self._open_note(self._notes_list.item(0))
        else:
            self._create_note()

    # ── UI construction ──────────────────────────────────────
    def _build_ui(self):
        self._status = self.statusBar()
        self._status.setStyleSheet(f"color: {COLORS['text_muted']}; background: {COLORS['deep_navy']}; "
                                   f"font-family: '{FONTS['mono']}'; font-size: {FONTS['size_sm']}px;")

        root = QWidget()
        root.setStyleSheet(f"background: {glass_bg_dark()};")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar ──
        top = QWidget()
        top.setStyleSheet(f"background: {glass_bg(200)}; border-bottom: 1px solid {glass_edge()};")
        top.setFixedHeight(52)
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(SPACING["lg"], 0, SPACING["lg"], 0)

        brand = QLabel("LOGBOOK")
        brand.setStyleSheet(f"color: {COLORS['seafoam']}; font-family: '{FONTS['mono']}'; "
                            f"font-size: {FONTS['size_lg']}px; font-weight: bold; letter-spacing: 2px; background: transparent;")
        top_lay.addWidget(brand)
        top_lay.addSpacing(SPACING["xl"])

        self._search = QLineEdit()
        self._search.setPlaceholderText("  Search notes…  (Ctrl+F)")
        self._search.setStyleSheet(self._input_style())
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._filter_notes)
        top_lay.addWidget(self._search, 1)

        new_btn = self._button("＋ New (Ctrl+N)")
        new_btn.clicked.connect(self._create_note)
        top_lay.addWidget(new_btn)

        outer.addWidget(top)

        # ── Splitter: notes list | editor | preview ──
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.setStyleSheet(f"QSplitter::handle {{ background: {glass_edge()}; }}")

        # Left: note list
        left = QWidget()
        left.setStyleSheet(f"background: {glass_bg_dark(160)};")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        list_header = QLabel("  NOTES")
        list_header.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; "
                                   f"font-size: {FONTS['size_xs']}px; padding: 6px 0; background: {glass_bg_dark(160)}; letter-spacing: 1px;")
        left_lay.addWidget(list_header)

        self._notes_list = QListWidget()
        self._notes_list.setStyleSheet(f"""
            QListWidget {{ background: {glass_bg_dark(160)}; border: none; color: {COLORS['hd_white']};
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px; }}
            QListWidget::item {{ padding: 8px 10px; border-left: 3px solid transparent; }}
            QListWidget::item:selected {{ background: {COLORS['surface_selected']}; border-left: 3px solid {COLORS['seafoam']}; }}
            QListWidget::item:hover:!selected {{ background: {COLORS['surface_hover']}; }}
        """)
        self._notes_list.currentItemChanged.connect(self._on_item_changed)
        left_lay.addWidget(self._notes_list, 1)

        self._splitter.addWidget(left)

        # Middle: editor
        self._editor = QTextEdit()
        self._editor.setPlaceholderText("Write markdown here…\n\n# Title\n\n## Section\n\n- bullet\n\n```python\nprint('hi')\n```")
        self._editor.setStyleSheet(f"""
            QTextEdit {{ background: {glass_bg()}; color: {COLORS['hd_white']};
                border: none; border-right: 1px solid {glass_edge()};
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_md']}px;
                padding: {SPACING['xl']}px; selection-background-color: {COLORS['surface_selected']}; }}
        """)
        self._editor.textChanged.connect(self._on_edit)
        self._splitter.addWidget(self._editor)

        # Right: preview
        right = QWidget()
        right.setStyleSheet(f"background: {glass_bg()};")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setStyleSheet(f"""
            QTextEdit {{ background: {glass_bg()}; color: {COLORS['text_secondary']};
                border: none; padding: {SPACING['xl']}px; }}
        """)
        right_lay.addWidget(self._preview)
        self._splitter.addWidget(right)

        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 3)
        self._splitter.setStretchFactor(2, 3)
        self._splitter.setSizes([260, 380, 420])
        outer.addWidget(self._splitter, 1)

        self._bind_shortcuts()

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{ background: {glass_bg()}; color: {COLORS['hd_white']};
                border: 1px solid {glass_edge()}; padding: 6px 10px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px; }}
            QLineEdit:focus {{ border-color: {COLORS['seafoam']}; }}
        """

    def _button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{ background: {glass_bg()}; color: {COLORS['seafoam']};
                border: 1px solid {glass_edge()}; padding: 6px 14px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px; }}
            QPushButton:hover {{ background: {COLORS['seafoam_deep']}; }}
        """)
        return btn

    def _bind_shortcuts(self):
        def shortcut(seq, fn):
            from PySide6.QtGui import QKeySequence, QShortcut
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(fn)
            return sc
        shortcut("Ctrl+N", self._create_note)
        shortcut("Ctrl+F", lambda: self._search.setFocus())
        shortcut("Ctrl+S", self._save_current)
        shortcut("Ctrl+Shift+P", self._toggle_preview)
        shortcut("Delete", self._delete_current)
        shortcut("Ctrl+R", self._rename_current)
        shortcut("F2", self._rename_current)

    # ── Note management ──────────────────────────────────────
    def _load_notes(self):
        self._notes.clear()
        self._notes_list.clear()
        os.makedirs(APP_DIR, exist_ok=True)
        for name in sorted(os.listdir(APP_DIR), key=str.lower):
            path = os.path.join(APP_DIR, name)
            if name.lower().endswith(".md") and os.path.isfile(path):
                note = Note(path)
                self._notes[path] = note
                self._notes_list.addItem(self._make_item(note))

    def _make_item(self, note: Note) -> QListWidgetItem:
        item = QListWidgetItem(f"{note.title}")
        item.setData(Qt.UserRole, note.path)
        item.setToolTip(note.path)
        return item

    def _create_note(self):
        title, ok = QInputDialog.getText(self, "New Note", "Note title:", text="Untitled")
        if not ok:
            return
        title = title.strip() or "Untitled"
        path = os.path.join(APP_DIR, Note.safe_filename(title) + ".md")
        counter = 2
        while path in self._notes or os.path.exists(path):
            path = os.path.join(APP_DIR, f"{Note.safe_filename(title)} {counter}.md")
            counter += 1
        note = Note(path)
        note.write(f"# {title}\n\n")
        self._notes[path] = note
        item = self._make_item(note)
        self._notes_list.addItem(item)
        self._notes_list.setCurrentItem(item)
        self._open_note(item)

    def _open_note(self, item: QListWidgetItem):
        if item is None:
            return
        path = item.data(Qt.UserRole)
        note = self._notes.get(path)
        if note is None:
            return
        self._flush_save()
        self._current_path = path
        self._dirty = False
        self._editor.blockSignals(True)
        self._editor.setPlainText(note.read())
        self._editor.blockSignals(False)
        self._update_preview()
        self._set_status(f"{note.title}  ·  saved {time.strftime('%H:%M:%S', time.localtime(note.mtime))}")

    def _on_item_changed(self, current, previous):
        if current is not None:
            self._open_note(current)

    def _on_edit(self):
        if self._current_path is None:
            return
        self._dirty = True
        self._update_preview()
        self._set_status("Editing… unsaved changes (auto-saves every 2s)")

    def _flush_save(self):
        if not self._dirty or self._current_path is None or self._saving:
            return
        note = self._notes.get(self._current_path)
        if note is None:
            return
        self._saving = True
        try:
            note.write(self._editor.toPlainText())
            self._dirty = False
            self._set_status(f"Saved  ·  {note.title}  ·  {time.strftime('%H:%M:%S')}")
        finally:
            self._saving = False

    def _save_current(self):
        self._flush_save()
        if self._current_path:
            self._set_status("Saved ✓")

    def _update_preview(self):
        text = self._editor.toPlainText()
        self._preview.setHtml(_render_markdown(text))

    def _toggle_preview(self):
        container = self._preview.parentWidget()
        if container is None:
            return
        if container.isVisible():
            container.hide()
        else:
            container.show()

    def _filter_notes(self, query: str):
        q = query.strip().lower()
        for i in range(self._notes_list.count()):
            item = self._notes_list.item(i)
            note = self._notes.get(item.data(Qt.UserRole))
            if note is None:
                continue
            match = q in note.title.lower()
            if not match and q and q in note.read().lower():
                match = True
            item.setHidden(not match)
            if match:
                item.setText(note.title)

    def _rename_current(self):
        if self._current_path is None:
            return
        note = self._notes[self._current_path]
        title, ok = QInputDialog.getText(self, "Rename Note", "New title:", text=note.title)
        if not ok or not title.strip():
            return
        self._flush_save()
        new_path = os.path.join(APP_DIR, Note.safe_filename(title) + ".md")
        counter = 2
        while new_path != note.path and (new_path in self._notes or os.path.exists(new_path)):
            new_path = os.path.join(APP_DIR, f"{Note.safe_filename(title)} {counter}.md")
            counter += 1
        if new_path != note.path:
            try:
                os.replace(note.path, new_path)
                del self._notes[note.path]
                self._notes[new_path] = Note(new_path)
                self._current_path = new_path
                self._refresh_list_selection(new_path)
            except OSError:
                QMessageBox.warning(self, "Rename", "Could not rename note.")

    def _delete_current(self):
        if self._current_path is None:
            return
        note = self._notes[self._current_path]
        if QMessageBox.question(self, "Delete Note", f"Delete '{note.title}'?") != QMessageBox.Yes:
            return
        try:
            os.remove(note.path)
        except OSError:
            pass
        del self._notes[note.path]
        self._refresh_list_selection(None)

    def _refresh_list_selection(self, select_path: str | None):
        self._notes_list.clear()
        for path in sorted(self._notes, key=str.lower):
            note = self._notes[path]
            item = self._make_item(note)
            self._notes_list.addItem(item)
            if path == select_path:
                self._notes_list.setCurrentItem(item)
        if select_path is None and self._notes_list.count() == 0:
            self._current_path = None
            self._editor.clear()
            self._preview.clear()

    def _set_status(self, text: str):
        self._status.showMessage(text)


def main():
    try:
        log = get_logger("APP")
        log.info("Logbook Notes starting")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Logbook")
    app.setOrganizationName("Nautilus")

    try:
        from core.icons import get_logo
        app.setWindowIcon(get_logo("logbook"))
    except Exception:
        pass

    try:
        app.setPalette(create_nautilus_palette())
        app.setStyleSheet(get_global_stylesheet())
    except Exception:
        pass

    font = QFont()
    font.setFamilies([FONTS.get("ui", "Segoe UI"), FONTS.get("mono", "JetBrains Mono")])
    font.setPointSize(FONTS.get("size_md", 12))
    app.setFont(font)

    window = LogbookWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
