import os
import re

from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.Abyssal.src.ui.styles import AbyssalTheme


class SearchWorker(QThread):
    result_found = Signal(str, int, str, str, str)  # file, line_num, line_text, match_text, context
    progress = Signal(int, int)  # current, total
    finished = Signal(int, float)  # total_matches, elapsed_time
    error = Signal(str)

    def __init__(self, root_path: str, pattern: str, case_sensitive: bool,
                 whole_word: bool, use_regex: bool, include_pattern: str,
                 exclude_pattern: str):
        super().__init__()
        self.root_path = root_path
        self.pattern = pattern
        self.case_sensitive = case_sensitive
        self.whole_word = whole_word
        self.use_regex = use_regex
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _match_file(self, filename: str) -> bool:
        if self.include_pattern:
            import fnmatch
            if not fnmatch.fnmatch(filename, self.include_pattern):
                return False
        if self.exclude_pattern:
            import fnmatch
            if fnmatch.fnmatch(filename, self.exclude_pattern):
                return False
        return True

    def _build_regex(self) -> re.Pattern:
        pattern = self.pattern
        if not self.use_regex:
            pattern = re.escape(pattern)
        if self.whole_word:
            pattern = r'\b' + pattern + r'\b'
        flags = 0 if self.case_sensitive else re.IGNORECASE
        return re.compile(pattern, flags)

    def run(self):
        import time
        start = time.time()
        try:
            regex = self._build_regex()
        except re.error as e:
            self.error.emit(f"Invalid regex: {e}")
            return

        all_files = []
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') or d in ('.git', '.github', '.vscode')]
            for f in files:
                if self._match_file(f):
                    all_files.append(os.path.join(root, f))

        total = len(all_files)
        matches = 0

        for i, filepath in enumerate(all_files):
            if self._cancelled:
                break
            try:
                with open(filepath, encoding='utf-8') as f:
                    lines = f.readlines()
            except (UnicodeDecodeError, OSError):
                try:
                    with open(filepath, encoding='latin-1') as f:
                        lines = f.readlines()
                except OSError:
                    continue

            for line_num, line in enumerate(lines, 1):
                if self._cancelled:
                    break
                for match in regex.finditer(line):
                    matches += 1
                    context_start = max(0, line_num - 2)
                    context_end = min(len(lines), line_num + 1)
                    context = ''.join(lines[context_start:context_end])
                    self.result_found.emit(
                        filepath, line_num, line.rstrip('\n'),
                        match.group(), context
                    )
            
            if i % 50 == 0:
                self.progress.emit(i + 1, total)

        elapsed = time.time() - start
        self.finished.emit(matches, elapsed)


class SearchResultItem(QTreeWidgetItem):
    def __init__(self, file_path: str, line_num: int, line_text: str, match_text: str, context: str):
        super().__init__()
        self.file_path = file_path
        self.line_num = line_num
        self.line_text = line_text
        self.match_text = match_text
        self.context = context
        self.setText(0, f"{os.path.basename(file_path)}:{line_num}")
        self.setToolTip(0, file_path)


class SearchPanel(QWidget):
    file_selected = Signal(str, int)  # file_path, line_number
    search_requested = Signal(str, bool, bool, bool, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AbyssalTheme.PANEL};")
        self._worker: SearchWorker | None = None
        self._root_path = os.path.expanduser("~")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            border-bottom: 1px solid {AbyssalTheme.BORDER};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        
        title = QLabel("SEARCH")
        title.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        # Search input
        search_widget = QWidget()
        search_widget.setFixedHeight(40)
        search_widget.setStyleSheet(f"background-color: {AbyssalTheme.PANEL}; border-bottom: 1px solid {AbyssalTheme.BORDER};")
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(8, 4, 8, 4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in files...")
        self.search_input.returnPressed.connect(self._start_search)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {AbyssalTheme.ACCENT}; }}
        """)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedWidth(80)
        self.search_btn.clicked.connect(self._start_search)
        self.search_btn.setStyleSheet(self._button_style())
        search_layout.addWidget(self.search_btn)
        layout.addWidget(search_widget)

        # Options
        options_widget = QWidget()
        options_widget.setFixedHeight(36)
        options_widget.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-bottom: 1px solid {AbyssalTheme.BORDER};")
        options_layout = QHBoxLayout(options_widget)
        options_layout.setContentsMargins(8, 4, 8, 4)
        options_layout.setSpacing(16)

        self.case_cb = QCheckBox("Aa")
        self.case_cb.setToolTip("Match Case")
        self.case_cb.setStyleSheet(self._checkbox_style())
        options_layout.addWidget(self.case_cb)

        self.word_cb = QCheckBox("Ww")
        self.word_cb.setToolTip("Match Whole Word")
        self.word_cb.setStyleSheet(self._checkbox_style())
        options_layout.addWidget(self.word_cb)

        self.regex_cb = QCheckBox(".*")
        self.regex_cb.setToolTip("Use Regular Expression")
        self.regex_cb.setStyleSheet(self._checkbox_style())
        options_layout.addWidget(self.regex_cb)

        options_layout.addStretch()

        self.include_input = QLineEdit()
        self.include_input.setPlaceholderText("files to include (e.g. *.py)")
        self.include_input.setFixedWidth(150)
        self.include_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 10px;
            }}
        """)
        options_layout.addWidget(self.include_input)

        self.exclude_input = QLineEdit()
        self.exclude_input.setPlaceholderText("files to exclude (e.g. *.min.js)")
        self.exclude_input.setFixedWidth(150)
        self.exclude_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 10px;
            }}
        """)
        options_layout.addWidget(self.exclude_input)

        layout.addWidget(options_widget)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {AbyssalTheme.BG};
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {AbyssalTheme.ACCENT};
            }}
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Results tree
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderHidden(True)
        self.results_tree.setStyleSheet(f"""
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
            }}
        """)
        self.results_tree.itemDoubleClicked.connect(self._on_result_double_click)
        self.results_tree.itemClicked.connect(self._on_result_click)
        layout.addWidget(self.results_tree)

        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setFixedHeight(24)
        self.status_label.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            padding: 0 8px;
            font-size: 10px;
            border-top: 1px solid {AbyssalTheme.BORDER};
        """)
        layout.addWidget(self.status_label)

    def _button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {AbyssalTheme.ACCENT};
                color: {AbyssalTheme.BG};
                border: none;
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {AbyssalTheme.ACCENT_LIGHT}; }}
            QPushButton:pressed {{ background-color: {AbyssalTheme.ACCENT_DIM}; }}
            QPushButton:disabled {{ background-color: {AbyssalTheme.BORDER}; color: {AbyssalTheme.TEXT_MUTED}; }}
        """

    def _checkbox_style(self) -> str:
        return f"""
            QCheckBox {{
                color: {AbyssalTheme.TEXT_DIM};
                font-size: 11px;
                font-weight: bold;
                spacing: 4px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 2px;
                background-color: {AbyssalTheme.BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {AbyssalTheme.ACCENT};
                border-color: {AbyssalTheme.ACCENT};
            }}
            QCheckBox::indicator:hover {{
                border-color: {AbyssalTheme.ACCENT};
            }}
        """

    def set_root_directory(self, path: str) -> None:
        self._root_path = path

    def _start_search(self):
        pattern = self.search_input.text().strip()
        if not pattern:
            return

        self.results_tree.clear()
        self.status_label.setText("Searching...")
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")

        self._worker = SearchWorker(
            self._root_path, pattern,
            self.case_cb.isChecked(),
            self.word_cb.isChecked(),
            self.regex_cb.isChecked(),
            self.include_input.text().strip(),
            self.exclude_input.text().strip()
        )
        self._worker.result_found.connect(self._add_result)
        self._worker.progress.connect(self._update_progress)
        self._worker.finished.connect(self._search_finished)
        self._worker.error.connect(self._search_error)
        self._worker.start()

    @Slot(str, int, str, str, str)
    def _add_result(self, file_path: str, line_num: int, line_text: str, match_text: str, context: str):
        item = SearchResultItem(file_path, line_num, line_text, match_text, context)
        self.results_tree.addTopLevelItem(item)

    @Slot(int, int)
    def _update_progress(self, current: int, total: int):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)

    @Slot(int, float)
    def _search_finished(self, matches: int, elapsed: float):
        self.progress_bar.hide()
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.status_label.setText(f"{matches} matches in {elapsed:.2f}s")

    @Slot(str)
    def _search_error(self, error: str):
        self.progress_bar.hide()
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.status_label.setText(f"Error: {error}")

    def _on_result_click(self, item: SearchResultItem):
        self.status_label.setText(f"{item.file_path}:{item.line_num}")

    def _on_result_double_click(self, item: SearchResultItem):
        self.file_selected.emit(item.file_path, item.line_num)

    def cancel_search(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1000)