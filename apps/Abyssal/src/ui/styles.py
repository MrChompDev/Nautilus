

class AbyssalTheme:
    BG = "#050D13"
    BG_DARK = "#030810"
    PANEL = "#0C1A2A"
    PANEL_ALT = "#0A1624"
    PANEL_HOVER = "#13253A"
    PANEL_ACTIVE = "#0E2238"
    ACCENT = "#00D4AA"
    ACCENT_DIM = "#00A88A"
    ACCENT_LIGHT = "#33FFD2"
    CORAL = "#FF6B4A"
    YELLOW = "#F0C040"
    BLUE = "#4AA8FF"
    PURPLE = "#B18AFF"
    TEXT = "#D8E2EC"
    TEXT_DIM = "#6A8EA8"
    TEXT_MUTED = "#3E5E78"
    WHITE = "#FFFFFF"
    BORDER = "#1A3352"
    BORDER_LIGHT = "#254565"
    SELECTION = "#1A3A5C"
    ACTIVE_TAB = "#050D13"
    INACTIVE_TAB = "#061018"
    STATUS_BAR = "#007A5E"
    STATUS_BAR_WARNING = "#B8860B"
    TITLE_BAR = "#040A12"
    SCROLLBAR_BG = "#0C1A2A"
    SCROLLBAR_HANDLE = "#2A4A6A"
    SCROLLBAR_HOVER = "#3A6A8A"
    SCROLLBAR_INACTIVE = "#1A334A"
    BREADCRUMB = "#0C1A2A"
    FIND_MATCH = "#515C6A"
    FIND_MATCH_CURRENT = "#FF6B4A"
    LINE_HIGHLIGHT = "#0A1A2A"
    LINE_NUM = "#3E5E78"
    LINE_NUM_CURRENT = "#8AAEC8"
    INDENT_GUIDE = "#1A3352"
    WHITESPACE = "#2A4A6A"
    ERROR_UNDERLINE = "#FF4444"
    WARNING_UNDERLINE = "#FFAA00"
    INFO_UNDERLINE = "#4AA8FF"

    @staticmethod
    def get_stylesheet():
        t = AbyssalTheme
        return f"""
            * {{
                font-family: "Segoe UI", "JetBrains Mono", "Consolas", "Courier New", monospace;
                font-size: 11px;
            }}

            QMainWindow, QWidget {{
                background-color: {t.BG};
                color: {t.TEXT};
            }}

            /* ── Menu Bar ── */
            QMenuBar {{
                background-color: {t.TITLE_BAR};
                color: {t.TEXT};
                border-bottom: 1px solid {t.BORDER};
                padding: 0;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 5px 12px;
                spacing: 3px;
            }}
            QMenuBar::item:selected {{
                background-color: {t.PANEL_HOVER};
            }}
            QMenuBar::item:pressed {{
                background-color: {t.ACCENT_DIM};
            }}
            QMenu {{
                background-color: {t.PANEL};
                color: {t.TEXT};
                border: 1px solid {t.BORDER_LIGHT};
                padding: 4px 0;
                border-radius: 4px;
            }}
            QMenu::item {{
                padding: 5px 24px 5px 10px;
                spacing: 12px;
                border: 1px solid transparent;
            }}
            QMenu::item:selected {{
                background-color: {t.PANEL_ACTIVE};
                border-color: {t.BORDER_LIGHT};
            }}
            QMenu::item:disabled {{
                color: {t.TEXT_MUTED};
            }}
            QMenu::separator {{
                height: 1px;
                background: {t.BORDER};
                margin: 4px 12px;
            }}
            QMenu::indicator {{
                width: 16px;
                height: 12px;
            }}

            /* ── Splitter ── */
            QSplitter::handle {{
                background-color: {t.BORDER};
            }}
            QSplitter::handle:horizontal {{
                width: 1px;
                min-width: 1px;
                max-width: 1px;
            }}
            QSplitter::handle:vertical {{
                height: 1px;
                min-height: 1px;
                max-height: 1px;
            }}
            QSplitter::handle:hover {{
                background-color: {t.ACCENT_DIM};
            }}

            /* ── Editor / Text ── */
            QPlainTextEdit, QTextEdit {{
                background-color: {t.BG};
                color: {t.TEXT};
                border: none;
                selection-background-color: {t.SELECTION};
                selection-color: {t.TEXT};
                caretprecision: 0.5;
            }}
            QPlainTextEdit:focus, QTextEdit:focus {{
                border: none;
            }}

            /* ── Scrollbars ── */
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                border: none;
                margin: 0;
                padding: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {t.SCROLLBAR_INACTIVE};
                min-height: 30px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t.SCROLLBAR_HOVER};
            }}
            QScrollBar::handle:vertical:pressed {{
                background: {t.SCROLLBAR_HOVER};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar::handle:vertical:disabled {{
                background: {t.SCROLLBAR_INACTIVE};
            }}
            QScrollBar:horizontal {{
                background: transparent;
                height: 10px;
                border: none;
                margin: 0;
                padding: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {t.SCROLLBAR_INACTIVE};
                min-width: 30px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {t.SCROLLBAR_HOVER};
            }}
            QScrollBar::handle:horizontal:pressed {{
                background: {t.SCROLLBAR_HOVER};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            QScrollBar:horizontal:disabled {{
                background: transparent;
            }}

            /* ── Tree View ── */
            QTreeView {{
                background-color: {t.PANEL};
                color: {t.TEXT};
                border: none;
                outline: none;
                show-decoration-selected: 0;
            }}
            QTreeView::item {{
                padding: 2px 0;
                border: none;
                min-height: 22px;
                margin: 0;
            }}
            QTreeView::item:hover {{
                background-color: {t.PANEL_HOVER};
            }}
            QTreeView::item:selected {{
                background-color: {t.SELECTION};
                color: {t.TEXT};
                border: none;
            }}
            QTreeView::branch {{
                background: {t.PANEL};
                border: none;
            }}
            QTreeView::item:disabled {{
                color: {t.TEXT_MUTED};
            }}

            /* ── Line Edit ── */
            QLineEdit {{
                background-color: {t.BG};
                color: {t.TEXT};
                border: 1px solid {t.BORDER};
                padding: 4px 8px;
                border-radius: 3px;
                selection-background-color: {t.ACCENT};
                selection-color: {t.BG};
                min-height: 24px;
            }}
            QLineEdit:focus {{
                border-color: {t.ACCENT};
                selection-background-color: {t.ACCENT_DIM};
            }}
            QLineEdit::placeholder {{
                color: {t.TEXT_MUTED};
            }}
            QLineEdit:disabled {{
                color: {t.TEXT_MUTED};
                background-color: {t.PANEL_ALT};
            }}

            /* ── Buttons ── */
            QPushButton {{
                background-color: transparent;
                color: {t.TEXT_DIM};
                border: 1px solid transparent;
                padding: 4px 10px;
                border-radius: 3px;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {t.TEXT};
                background-color: {t.PANEL_HOVER};
                border-color: {t.BORDER_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {t.ACCENT_DIM};
                color: {t.BG};
            }}
            QPushButton:checked {{
                background-color: {t.ACCENT_DIM};
                color: {t.BG};
                border-color: {t.ACCENT_DIM};
            }}
            QPushButton:disabled {{
                color: {t.TEXT_MUTED};
                background: transparent;
            }}

            /* ── Tab Widget ── */
            QTabWidget::pane {{
                border: none;
                background-color: {t.BG};
            }}
            QTabBar {{
                background-color: {t.INACTIVE_TAB};
            }}

            /* ── Tooltips ── */
            QToolTip {{
                background-color: {t.PANEL};
                color: {t.TEXT};
                border: 1px solid {t.BORDER_LIGHT};
                padding: 4px 8px;
                border-radius: 3px;
                opacity: 230;
            }}
            QToolTip::label {{
                background: transparent;
                border: none;
                padding: 0;
            }}

            /* ── Status Bar ── */
            QStatusBar {{
                background-color: {t.STATUS_BAR};
                color: {t.BG};
                border: none;
            }}
            QStatusBar::item {{
                border: none;
                padding: 0 6px;
            }}

            /* ── Label ── */
            QLabel {{
                background: transparent;
                border: none;
                padding: 0;
            }}

            /* ── GroupBox ── */
            QGroupBox {{
                border: 1px solid {t.BORDER};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }}

            /* ── ProgressBar ── */
            QProgressBar {{
                background-color: {t.PANEL_ALT};
                border: 1px solid {t.BORDER};
                border-radius: 3px;
                text-align: center;
                color: {t.TEXT_DIM};
                min-height: 16px;
            }}
            QProgressBar::chunk {{
                background-color: {t.ACCENT};
                border-radius: 2px;
            }}
        """
