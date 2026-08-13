from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from apps.Abyssal.src.ui.styles import AbyssalTheme


class NotificationBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AbyssalTheme.BG};
                border-top: 1px solid {AbyssalTheme.BORDER};
                border-bottom: 1px solid {AbyssalTheme.BORDER};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel("⚠")
        self.icon_label.setStyleSheet(f"color: {AbyssalTheme.YELLOW}; font-size: 12px;")
        layout.addWidget(self.icon_label)

        self.message_label = QLabel("Ready")
        self.message_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(self.message_label)

        layout.addStretch()

        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {AbyssalTheme.TEXT_DIM};
                border: none;
                border-radius: 2px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {AbyssalTheme.PANEL_HOVER};
                color: {AbyssalTheme.TEXT};
            }}
        """)
        self.clear_btn.clicked.connect(self.clear)
        layout.addWidget(self.clear_btn)

    def show_message(self, message: str, type: str = "info"):
        if type == "error":
            self.icon_label.setText("✗")
            self.icon_label.setStyleSheet(f"color: {AbyssalTheme.CORAL}; font-size: 12px;")
        elif type == "warning":
            self.icon_label.setText("⚠")
            self.icon_label.setStyleSheet(f"color: {AbyssalTheme.YELLOW}; font-size: 12px;")
        elif type == "success":
            self.icon_label.setText("✓")
            self.icon_label.setStyleSheet(f"color: {AbyssalTheme.ACCENT}; font-size: 12px;")
        else:
            self.icon_label.setText("ℹ")
            self.icon_label.setStyleSheet(f"color: {AbyssalTheme.BLUE}; font-size: 12px;")

        self.message_label.setText(message)
        self.setVisible(True)

    def clear(self):
        self.setVisible(False)
        self.message_label.setText("Ready")
        self.icon_label.setText("⚠")
        self.icon_label.setStyleSheet(f"color: {AbyssalTheme.YELLOW}; font-size: 12px;")


class GitBadge(QLabel):
    def __init__(self, status: str = "❌", parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT_DIM};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 2px;
                font-size: 9px;
                font-weight: bold;
                padding: 0 4px;
            }}
        """)
        self.setText(status)

    def update_status(self, status: str):
        self.setText(status)
        if status == "✅ Clean":
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {AbyssalTheme.BG};
                    color: {AbyssalTheme.ACCENT};
                    border: 1px solid {AbyssalTheme.ACCENT};
                    border-radius: 2px;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 0 4px;
                }}
            """)
        elif status == "⚠ Modified":
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {AbyssalTheme.BG};
                    color: {AbyssalTheme.YELLOW};
                    border: 1px solid {AbyssalTheme.YELLOW};
                    border-radius: 2px;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 0 4px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {AbyssalTheme.BG};
                    color: {AbyssalTheme.TEXT_DIM};
                    border: 1px solid {AbyssalTheme.BORDER};
                    border-radius: 2px;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 0 4px;
                }}
            """)


class StatusBar(QWidget):
    status_changed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AbyssalTheme.PANEL};
                border-top: 1px solid {AbyssalTheme.BORDER};
                border-bottom: 1px solid {AbyssalTheme.BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        # Left side - Git status
        self.git_badge = GitBadge()
        layout.addWidget(self.git_badge)

        # Middle - Position and language
        self.position_label = QLabel("Ln 1, Col 1")
        self.position_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(self.position_label)

        self.separator1 = QLabel("│")
        self.separator1.setStyleSheet(f"color: {AbyssalTheme.BORDER_LIGHT}; font-size: 9px;")
        layout.addWidget(self.separator1)

        self.language_label = QLabel("Plain Text")
        self.language_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(self.language_label)

        layout.addStretch()

        # Right side - Notifications
        self.notification_bar = NotificationBar()
        layout.addWidget(self.notification_bar)

        self.separator2 = QLabel("│")
        self.separator2.setStyleSheet(f"color: {AbyssalTheme.BORDER_LIGHT}; font-size: 9px;")
        layout.addWidget(self.separator2)

        # Encoding, EOL, Indent indicators
        self.encoding_label = QLabel("UTF-8")
        self.encoding_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_MUTED}; font-size: 9px;")
        layout.addWidget(self.encoding_label)

        self.separator3 = QLabel("│")
        self.separator3.setStyleSheet(f"color: {AbyssalTheme.BORDER_LIGHT}; font-size: 9px;")
        layout.addWidget(self.separator3)

        self.eol_label = QLabel("LF")
        self.eol_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_MUTED}; font-size: 9px;")
        layout.addWidget(self.eol_label)

        self.separator4 = QLabel("│")
        self.separator4.setStyleSheet(f"color: {AbyssalTheme.BORDER_LIGHT}; font-size: 9px;")
        layout.addWidget(self.separator4)

        self.indent_label = QLabel("Spaces: 4")
        self.indent_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_MUTED}; font-size: 9px;")
        layout.addWidget(self.indent_label)

        # Git button
        self.git_button = QPushButton("Git")
        self.git_button.setFixedHeight(22)
        self.git_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.PANEL_ALT};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {AbyssalTheme.PANEL_HOVER};
                border-color: {AbyssalTheme.ACCENT};
                color: {AbyssalTheme.ACCENT};
            }}
        """)
        layout.addWidget(self.git_button)

    def update_position(self, line: int, col: int):
        self.position_label.setText(f"Ln {line}, Col {col}")

    def update_language(self, lang: str):
        from apps.Abyssal.src.engines.highlighter import LANG_NAMES
        name = LANG_NAMES.get(lang, lang.title())
        self.language_label.setText(name)

    def update_encoding(self, enc: str = "UTF-8"):
        self.encoding_label.setText(enc)

    def update_eol(self, eol: str = "LF"):
        self.eol_label.setText(eol)

    def update_indent(self, spaces: int = 4):
        self.indent_label.setText(f"Spaces: {spaces}")

    def set_git_status(self, status: str):
        self.git_badge.update_status(status)

    def show_notification(self, message: str, type: str = "info"):
        self.notification_bar.show_message(message, type)