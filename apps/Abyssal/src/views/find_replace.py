from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from apps.Abyssal.src.ui.styles import AbyssalTheme


class FindReplaceBar(QWidget):
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            border-bottom: 1px solid {AbyssalTheme.BORDER};
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Find")
        self.search_bar.setFixedWidth(260)
        self.search_bar.returnPressed.connect(self._find_next)
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 3px 8px;
                selection-background-color: {AbyssalTheme.ACCENT};
                selection-color: {AbyssalTheme.BG};
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {AbyssalTheme.ACCENT};
            }}
        """)
        layout.addWidget(self.search_bar)

        self.result_label = QLabel("No results")
        self.result_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px; padding: 0 4px;")
        layout.addWidget(self.result_label)

        layout.addStretch()

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace")
        self.replace_input.setFixedWidth(200)
        self.replace_input.hide()
        self.replace_input.setStyleSheet(self.search_bar.styleSheet())
        layout.addWidget(self.replace_input)

        self.case_btn = self._toggle_btn("Aa", "Match Case")
        self.word_btn = self._toggle_btn("\u2759\u2759", "Match Whole Word")
        self.regex_btn = self._toggle_btn(".*", "Use Regular Expression")
        layout.addWidget(self.case_btn)
        layout.addWidget(self.word_btn)
        layout.addWidget(self.regex_btn)

        self.find_next_btn = self._icon_btn("\u25BC", "Find Next")
        self.find_prev_btn = self._icon_btn("\u25B2", "Find Previous")
        layout.addWidget(self.find_prev_btn)
        layout.addWidget(self.find_next_btn)

        self.replace_btn = QPushButton("Replace")
        self.replace_btn.hide()
        self.replace_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                padding: 3px 10px;
                border-radius: 3px;
                font-size: 10px;
            }}
            QPushButton:hover {{ border-color: {AbyssalTheme.ACCENT}; color: {AbyssalTheme.ACCENT}; }}
        """)
        layout.addWidget(self.replace_btn)

        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.hide()
        self.replace_all_btn.setStyleSheet(self.replace_btn.styleSheet())
        layout.addWidget(self.replace_all_btn)

        close_btn = self._icon_btn("\u2715", "Close")
        close_btn.clicked.connect(self._close)
        layout.addWidget(close_btn)

        self.find_next_btn.clicked.connect(self._find_next)
        self.find_prev_btn.clicked.connect(self._find_prev)

    def _toggle_btn(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setToolTip(tooltip)
        btn.setFixedSize(26, 22)
        btn.setFont(QFont("Segoe UI", 9))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT_DIM};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 0 4px;
            }}
            QPushButton:checked {{
                background-color: {AbyssalTheme.ACCENT};
                color: {AbyssalTheme.BG};
                border-color: {AbyssalTheme.ACCENT};
            }}
            QPushButton:hover {{ border-color: {AbyssalTheme.ACCENT}; color: {AbyssalTheme.ACCENT}; }}
        """)
        return btn

    def _icon_btn(self, icon: str, tooltip: str) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(26, 22)
        btn.setToolTip(tooltip)
        btn.setFont(QFont("Segoe UI Symbol", 9))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
            }}
            QPushButton:hover {{ border-color: {AbyssalTheme.ACCENT}; color: {AbyssalTheme.ACCENT}; }}
            QPushButton:pressed {{ background-color: {AbyssalTheme.ACCENT_DIM}; color: {AbyssalTheme.BG}; }}
        """)
        return btn

    def show_replace(self) -> None:
        self.replace_input.show()
        self.replace_btn.show()
        self.replace_all_btn.show()
        self.setFixedHeight(76)

    def hide_replace(self) -> None:
        self.replace_input.hide()
        self.replace_btn.hide()
        self.replace_all_btn.hide()
        self.setFixedHeight(38)

    def toggle_replace(self) -> None:
        if self.replace_input.isVisible():
            self.hide_replace()
        else:
            self.show_replace()

    def _find_next(self) -> None:
        pass

    def _find_prev(self) -> None:
        pass

    def _close(self) -> None:
        self.hide()
        self.close_requested.emit()