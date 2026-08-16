import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from apps.Abyssal.src.config.workspace import WorkspaceConfig
from apps.Abyssal.src.ui.editor import AbyssalEditor
from apps.Abyssal.src.ui.styles import AbyssalTheme
from apps.Abyssal.src.ui.terminal import AbyssalTerminal
from apps.Abyssal.src.views.activity_bar import ActivityBar
from apps.Abyssal.src.views.breadcrumb import BreadcrumbBar
from apps.Abyssal.src.views.find_replace import FindReplaceBar
from apps.Abyssal.src.views.kraken_chat import KrakenChatPanel
from apps.Abyssal.src.views.palette import CommandPalette
from apps.Abyssal.src.views.sidebar import Sidebar
from apps.Abyssal.src.views.status_bar import StatusBar
from apps.Abyssal.src.views.tab_bar import TabBar


class AbyssalMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Abyssal Editor")
        self.setMinimumSize(1024, 600)
        self.resize(1400, 900)

        self._editors = {}
        self._current_file = None
        self._switching = False

        self._workspace = WorkspaceConfig(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
        )

        self._build_menu_bar()
        self._build_ui()
        self._setup_shortcuts()
        self._connect_signals()
        self._workspace._load()

        if not self._editors:
            self._new_file()

    # ── Menu Bar ──────────────────────────────────

    def _build_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("New File", self._new_file, "Ctrl+N")
        file_menu.addAction("Open File...", self._open_file, "Ctrl+O")
        file_menu.addAction("Save", self._save_current, "Ctrl+S")
        file_menu.addAction("Save As...", self._save_as, "Ctrl+Shift+S")
        file_menu.addSeparator()
        file_menu.addAction("Close Tab", self._close_current_tab, "Ctrl+W")
        file_menu.addSeparator()
        file_menu.addAction("Run File", self._run_file, "F5")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close, "Alt+F4")

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction("Undo", lambda: self.active_editor.undo(), "Ctrl+Z")
        edit_menu.addAction("Redo", lambda: self.active_editor.redo(), "Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction("Cut", lambda: self.active_editor.cut(), "Ctrl+X")
        edit_menu.addAction("Copy", lambda: self.active_editor.copy(), "Ctrl+C")
        edit_menu.addAction("Paste", lambda: self.active_editor.paste(), "Ctrl+V")
        edit_menu.addSeparator()
        edit_menu.addAction("Select All", lambda: self.active_editor.selectAll(), "Ctrl+A")
        edit_menu.addSeparator()
        edit_menu.addAction("Find", self._show_find, "Ctrl+F")
        edit_menu.addAction("Find and Replace", self._show_find_replace, "Ctrl+H")
        edit_menu.addAction("Go to Line...", self._go_to_line, "Ctrl+G")

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("Toggle Sidebar", self._toggle_sidebar, "Ctrl+B")
        view_menu.addAction("Toggle Terminal", self._toggle_terminal, "Ctrl+`")
        view_menu.addAction("Toggle Kraken Chat", self._toggle_chat, "Ctrl+Shift+C")
        view_menu.addSeparator()
        view_menu.addAction("Toggle Word Wrap", self._toggle_word_wrap)

        # Go menu
        go_menu = menubar.addMenu("&Go")
        go_menu.addAction("Go to Line...", self._go_to_line, "Ctrl+G")
        go_menu.addAction("Go to Symbol...", self._go_to_symbol)

        # Run menu
        run_menu = menubar.addMenu("&Run")
        run_menu.addAction("Run File", self._run_file, "F5")
        run_menu.addAction("Stop", self._stop_terminal)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("About", self._show_about)

    def _show_about(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About Abyssal",
            "<h2>Abyssal Editor v2.0</h2>"
            "<p>High-density, low-latency text editor for Nautilus OS</p>"
            "<p>Built with PySide6 | VS Code-inspired architecture</p>"
            "<p>Keyboard Shortcuts:</p>"
            "<ul>"
            "<li>Ctrl+N - New File</li>"
            "<li>Ctrl+O - Open File</li>"
            "<li>Ctrl+S - Save</li>"
            "<li>Ctrl+F - Find</li>"
            "<li>Ctrl+H - Find &amp; Replace</li>"
            "<li>Ctrl+G - Go to Line</li>"
            "<li>Ctrl+Shift+P - Command Palette</li>"
            "<li>F5 - Run File</li>"
            "<li>Ctrl+B - Toggle Sidebar</li>"
            "<li>Ctrl+` - Toggle Terminal</li>"
            "<li>Ctrl+Shift+C - Toggle Kraken Chat</li>"
            "</ul>"
        )

    # ── Build UI ──────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"""
            QWidget {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
            }}
        """)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        outer = QHBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.activity_bar = ActivityBar()
        outer.addWidget(self.activity_bar)

        self.sidebar = Sidebar()
        outer.addWidget(self.sidebar, 1)

        right_panel = QWidget()
        right_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.tab_bar = TabBar()
        right_layout.addWidget(self.tab_bar)

        self.breadcrumb = BreadcrumbBar()
        right_layout.addWidget(self.breadcrumb)

        self.find_bar = FindReplaceBar()
        self.find_bar.hide()
        right_layout.addWidget(self.find_bar)

        self.editor_terminal_splitter = QSplitter(Qt.Vertical)
        self.editor_terminal_splitter.setHandleWidth(1)

        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        self.editor_stack = {}

        self.active_editor = AbyssalEditor()
        self.editor_stack["__default__"] = self.active_editor
        editor_layout.addWidget(self.active_editor)

        self.terminal = AbyssalTerminal()
        self.terminal.hide()

        self.editor_terminal_splitter.addWidget(self.editor_container)
        self.editor_terminal_splitter.addWidget(self.terminal)
        self.editor_terminal_splitter.setStretchFactor(0, 3)
        self.editor_terminal_splitter.setStretchFactor(1, 1)

        right_layout.addWidget(self.editor_terminal_splitter, 1)

        outer.addWidget(right_panel, 1)

        self.kraken_chat = KrakenChatPanel()
        self.kraken_chat.set_workspace(self._workspace_root())
        self.kraken_chat.hide()
        self.kraken_chat.close_requested.connect(self._toggle_chat)
        outer.addWidget(self.kraken_chat)

        main_layout.addLayout(outer, 1)

        self.palette = CommandPalette()
        self._populate_palette()

        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)

        self._show_welcome()

    def _show_welcome(self):
        self.active_editor.setReadOnly(True)
        self.active_editor.setPlainText(
            "\n"
            "  Abyssal Editor v2.0\n"
            "  High-density, low-latency text editing for Chomp OS\n"
            "  Architecture: VS Code-inspired service layer\n"
            "\n"
            "  Quick Start\n"
            "  ──────────\n"
            "  Ctrl+Shift+P    Command Palette\n"
            "  Ctrl+P          Quick Open File\n"
            "  Ctrl+B          Toggle Sidebar\n"
            "  Ctrl+`          Toggle Terminal\n"
            "  Ctrl+Shift+C    Toggle Kraken Chat\n"
            "  Ctrl+N          New File\n"
            "  Ctrl+O          Open File\n"
            "  Ctrl+S          Save\n"
            "  Ctrl+F          Find\n"
            "  Ctrl+H          Find & Replace\n"
            "  Ctrl+G          Go to Line\n"
            "  F5 / Ctrl+R     Run Active File\n"
            "\n"
            "  Open a file or create a new one to begin.\n"
        )
        self.active_editor.moveCursor(self.active_editor.textCursor().MoveOperation.Start)

    def _new_file(self):
        existing = [f for f in self._editors if f.startswith("Untitled")]
        idx = len(existing) + 1
        name = f"Untitled-{idx}"

        editor = AbyssalEditor()
        editor.file_path = None
        editor.set_language("text")
        self._editors[name] = editor

        self.tab_bar.add_tab(name, "text")
        self._switch_to_editor(name)
        self.status_bar.show_notification(f"New file: {name}")

    def _open_file(self, path: str | None = None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Open File", "",
                "All Files (*);;Python (*.py);;JavaScript (*.js);;C/C++ (*.c *.cpp);;HTML (*.html);;CSS (*.css);;Markdown (*.md);;JSON (*.json);;Shell (*.sh)"
            )
            if not path:
                return

        for name, editor in self._editors.items():
            if getattr(editor, 'file_path', None) == path:
                self._switch_to_editor(name)
                return

        editor = AbyssalEditor()
        editor.open_file(path)
        self._editors[path] = editor
        self.tab_bar.add_tab(path, editor.language)
        self._switch_to_editor(path)
        self.status_bar.update_language(editor.language)

    def _switch_to_editor(self, name: str):
        if name not in self._editors or self._switching:
            return

        self._switching = True
        try:
            editor = self._editors[name]
            self.active_editor = editor
            self._current_file = name

            if name != "__default__":
                self.kraken_chat.set_workspace(self._workspace_root())

            layout = self.editor_container.layout()
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()

            layout.addWidget(editor)
            editor.show()
            editor.setFocus()

            self.tab_bar.select_tab(name)

            self.breadcrumb.set_path(name)
            self.status_bar.update_language(editor.language)
            self.status_bar.update_position(
                editor.textCursor().blockNumber() + 1,
                editor.textCursor().columnNumber() + 1,
            )
        finally:
            self._switching = False

    def _close_tab(self, name: str):
        if name not in self._editors:
            return

        editor = self._editors[name]
        if editor.document().isModified():
            self.status_bar.show_notification(f"Unsaved changes in {os.path.basename(name)}")

        editor.setParent(None)
        editor.deleteLater()
        del self._editors[name]
        self.tab_bar.close_tab(name)

        if not self._editors:
            self._new_file()

    def _save_current(self):
        if self.active_editor:
            if self.active_editor.save_file():
                self.status_bar.show_notification("File saved")

    def _save_as(self):
        if self.active_editor:
            self.active_editor.save_file_as()

    def _run_file(self):
        if self.active_editor and self.active_editor.file_path:
            self.active_editor.save_file()
            self.terminal.show()
            self.terminal.setFocus()
            self.terminal.execute_command(f"python {self.active_editor.file_path}")

    def _stop_terminal(self):
        if hasattr(self.terminal, 'cleanup'):
            self.terminal.cleanup()
        self.terminal.hide()

    def _go_to_line(self):
        if not self.active_editor:
            return
        line, ok = QInputDialog.getInt(
            self, "Go to Line", "Line number:",
            self.active_editor.textCursor().blockNumber() + 1,
            1, self.active_editor.document().blockCount()
        )
        if ok and line > 0:
            cursor = self.active_editor.textCursor()
            block = self.active_editor.document().findBlockByLineNumber(line - 1)
            if block.isValid():
                cursor.setPosition(block.position())
                self.active_editor.setTextCursor(cursor)
                self.active_editor.centerCursor()
                self.status_bar.update_position(line, 1)

    def _go_to_symbol(self):
        self.status_bar.show_notification("Symbol navigation coming soon")

    def _toggle_word_wrap(self):
        if self.active_editor:
            wrap_mode = self.active_editor.lineWrapMode()
            if wrap_mode == self.active_editor.LineWrapMode.NoWrap:
                self.active_editor.setLineWrapMode(self.active_editor.LineWrapMode.WidgetWidth)
                self.status_bar.show_notification("Word wrap: ON")
            else:
                self.active_editor.setLineWrapMode(self.active_editor.LineWrapMode.NoWrap)
                self.status_bar.show_notification("Word wrap: OFF")

    # ── Signals ──────────────────────────────────────

    def _connect_signals(self):
        self.activity_bar.panel_changed.connect(self._on_panel_change)
        self.sidebar.file_selected.connect(self._open_file)
        self.tab_bar.tab_changed.connect(self._switch_to_editor)
        self.tab_bar.tab_closed.connect(self._close_tab)
        self.palette.command_selected.connect(self._on_palette_command)
        self.find_bar.close_requested.connect(self._hide_find)
        self.find_bar.find_next_btn.clicked.connect(self._find_next)
        self.find_bar.find_prev_btn.clicked.connect(self._find_prev)
        self.find_bar.replace_btn.clicked.connect(self._replace_current)
        self.find_bar.replace_all_btn.clicked.connect(self._replace_all)
        self.find_bar.search_bar.returnPressed.connect(self._find_next)

    def _on_panel_change(self, name):
        if name == "settings":
            self.sidebar.show_panel("settings")
        elif name == "extensions":
            self.sidebar.show_panel("extensions")
        elif name == "search":
            self.sidebar.show_panel("search")
        elif name == "explorer":
            self.sidebar.show_panel("explorer")
        elif name == "git":
            pass

    # ── Shortcuts ─────────────────────────────────────

    def _setup_shortcuts(self):
        shortcuts = {
            "Ctrl+S": self._save_current,
            "Ctrl+Shift+S": self._save_as,
            "Ctrl+N": self._new_file,
            "Ctrl+O": self._open_file,
            "Ctrl+Shift+P": self._show_palette,
            "Ctrl+P": self._show_palette,
            "F5": self._run_file,
            "Ctrl+R": self._run_file,
            "Ctrl+B": self._toggle_sidebar,
            "Ctrl+`": self._toggle_terminal,
            "Ctrl+Shift+C": self._toggle_chat,
            "Ctrl+F": self._show_find,
            "Ctrl+H": self._show_find_replace,
            "Ctrl+W": self._close_current_tab,
            "Ctrl+G": self._go_to_line,
            "Escape": self._hide_find,
        }

        for key, slot in shortcuts.items():
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(slot)

    def _toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()

    def _toggle_terminal(self):
        if self.terminal.isVisible():
            self.terminal.hide()
        else:
            self.terminal.show()
            self.terminal.setFocus()

    def _workspace_root(self) -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if self._current_file and self._current_file != "__default__":
            folder = os.path.dirname(self._current_file)
            if folder and os.path.isdir(folder):
                return folder
        return project_root

    def _toggle_chat(self):
        if self.kraken_chat.isVisible():
            self.kraken_chat.hide()
        else:
            self.kraken_chat.set_workspace(self._workspace_root())
            self.kraken_chat.show()
            self.kraken_chat.focus_input()

    def _show_palette(self):
        self.palette.show()

    def _show_find(self):
        self.find_bar.hide_replace()
        self.find_bar.show()
        self.find_bar.search_bar.setFocus()
        cursor = self.active_editor.textCursor()
        if cursor.hasSelection():
            self.find_bar.search_bar.setText(cursor.selectedText())

    def _show_find_replace(self):
        self.find_bar.show_replace()
        self.find_bar.show()
        self.find_bar.search_bar.setFocus()
        cursor = self.active_editor.textCursor()
        if cursor.hasSelection():
            self.find_bar.search_bar.setText(cursor.selectedText())

    def _hide_find(self):
        self.find_bar.hide()

    def _find_next(self):
        text = self.find_bar.search_bar.text()
        case = self.find_bar.case_btn.isChecked()
        word = self.find_bar.word_btn.isChecked()
        regex = self.find_bar.regex_btn.isChecked()
        found = self.active_editor.find_next(text, case, word, regex)
        if not found:
            self.find_bar.result_label.setText("No results")
        else:
            self.find_bar.result_label.setText("")

    def _find_prev(self):
        text = self.find_bar.search_bar.text()
        case = self.find_bar.case_btn.isChecked()
        word = self.find_bar.word_btn.isChecked()
        regex = self.find_bar.regex_btn.isChecked()
        found = self.active_editor.find_prev(text, case, word, regex)
        if not found:
            self.find_bar.result_label.setText("No results")
        else:
            self.find_bar.result_label.setText("")

    def _replace_current(self):
        replacement = self.find_bar.replace_input.text()
        self.active_editor.replace_current(replacement)
        self._find_next()

    def _replace_all(self):
        text = self.find_bar.search_bar.text()
        replacement = self.find_bar.replace_input.text()
        case = self.find_bar.case_btn.isChecked()
        word = self.find_bar.word_btn.isChecked()
        regex = self.find_bar.regex_btn.isChecked()
        count = self.active_editor.replace_all(text, replacement, case, word, regex)
        self.find_bar.result_label.setText(f"Replaced {count} occurrences")

    def _close_current_tab(self):
        if self.active_editor and self._current_file:
            self._close_tab(self._current_file)

    # ── Palette Commands ──────────────────────────────

    def _populate_palette(self):
        cmds = [
            ("New File", "Ctrl+N"),
            ("Open File...", "Ctrl+O"),
            ("Save", "Ctrl+S"),
            ("Save As...", "Ctrl+Shift+S"),
            ("Run File", "F5"),
            ("Toggle Sidebar", "Ctrl+B"),
            ("Toggle Terminal", "Ctrl+`"),
            ("Toggle Kraken Chat", "Ctrl+Shift+C"),
            ("Toggle Word Wrap", ""),
            ("Find", "Ctrl+F"),
            ("Find and Replace", "Ctrl+H"),
            ("Go to Line...", "Ctrl+G"),
            ("Close Tab", "Ctrl+W"),
            ("Command Palette", "Ctrl+Shift+P"),
            ("Explorer", "Ctrl+Shift+E"),
            ("Search in Files", "Ctrl+Shift+F"),
            ("About", ""),
        ]
        for name, shortcut in cmds:
            self.palette.add_command(name, shortcut)

    def _on_palette_command(self, name: str):
        dispatch = {
            "New File": self._new_file,
            "Open File...": self._open_file,
            "Save": self._save_current,
            "Save As...": self._save_as,
            "Run File": self._run_file,
            "Toggle Sidebar": self._toggle_sidebar,
            "Toggle Terminal": self._toggle_terminal,
            "Toggle Kraken Chat": self._toggle_chat,
            "Toggle Word Wrap": self._toggle_word_wrap,
            "Find": self._show_find,
            "Find and Replace": self._show_find_replace,
            "Go to Line...": self._go_to_line,
            "Close Tab": self._close_current_tab,
            "Command Palette": self._show_palette,
            "Explorer": lambda: (self.sidebar.show_panel("explorer"), self.activity_bar.activate_panel("explorer")),
            "Search in Files": lambda: (self.sidebar.show_panel("search"), self.activity_bar.activate_panel("search")),
            "About": self._show_about,
        }
        if name in dispatch:
            dispatch[name]()

    def closeEvent(self, event):
        if hasattr(self, "terminal") and hasattr(self.terminal, "cleanup"):
            self.terminal.cleanup()
        if hasattr(self, "kraken_chat") and hasattr(self.kraken_chat, "_worker"):
            worker = self.kraken_chat._worker
            if worker is not None and worker.isRunning():
                worker.wait(1000)
        super().closeEvent(event)