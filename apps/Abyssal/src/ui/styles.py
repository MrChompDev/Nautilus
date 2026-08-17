

from core.theme import (
    COLORS,
    RADIUS_LG,
    RADIUS_MD,
    glass_bg,
    glass_bg_dark,
    glass_edge,
    glass_sheen,
    hex_to_rgba,
)


class AbyssalTheme:
    BG = "#050D13"
    BG_DARK = "#030810"
    PANEL = "#0C1A2A"
    PANEL_ALT = "#0A1624"
    PANEL_HOVER = "#13253A"
    PANEL_ACTIVE = COLORS["slate_navy"]
    ACCENT = COLORS["seafoam"]
    ACCENT_DIM = COLORS["seafoam_dim"]
    ACCENT_LIGHT = COLORS["seafoam_glow"]
    CORAL = COLORS["coral"]
    YELLOW = COLORS["amber"]
    BLUE = COLORS["text_secondary"]
    PURPLE = COLORS["text_bright"]
    TEXT = COLORS["hd_white"]
    TEXT_DIM = COLORS["text_muted"]
    WHITE = COLORS["text_bright"]
    TEXT_MUTED = COLORS["text_muted"]
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

    glass_bg = glass_bg(170)
    glass_bg_dark = glass_bg_dark(140)
    glass_edge = glass_edge()
    glass_sheen = glass_sheen()

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
                background: {glass_bg(190)};
                color: {t.TEXT};
                border-bottom: 1px solid {glass_edge()};
                padding: 0;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 5px 12px;
                spacing: 3px;
                border-radius: {RADIUS_MD};
            }}
            QMenuBar::item:selected {{
                background: {glass_bg(160)};
                border-color: {glass_edge()};
            }}
            QMenuBar::item:pressed {{
                background: {hex_to_rgba(COLORS["seafoam_deep"], 180)};
                color: {t.ACCENT};
            }}
            QMenu {{
                background: {glass_bg(230)};
                color: {t.TEXT};
                border: 1px solid {glass_edge()};
                padding: 4px 0;
                border-radius: {RADIUS_MD};
            }}
            QMenu::item {{
                padding: 5px 24px 5px 10px;
                spacing: 12px;
                border: none;
                border-radius: 0px;
            }}
            QMenu::item:selected {{
                background: {hex_to_rgba(COLORS["seafoam_deep"], 180)};
                color: {t.ACCENT};
            }}
            QMenu::item:disabled {{
                color: {t.TEXT_MUTED};
            }}
            QMenu::separator {{
                height: 1px;
                background: {glass_edge()};
                margin: 4px 12px;
            }}
            QMenu::indicator {{
                width: 16px;
                height: 12px;
            }}

            /* ── Splitter ── */
            QSplitter::handle {{
                background: {glass_edge(40)};
                border-radius: 1px;
            }}
            QSplitter::handle:horizontal {{
                width: 3px;
                min-width: 3px;
                max-width: 3px;
            }}
            QSplitter::handle:vertical {{
                height: 3px;
                min-height: 3px;
                max-height: 3px;
            }}
            QSplitter::handle:hover {{
                background: {COLORS["seafoam_dim"]};
            }}

            /* ── Editor / Text ── */
            QPlainTextEdit, QTextEdit {{
                background-color: {hex_to_rgba(COLORS["terminal_bg"], 200)};
                color: {t.TEXT};
                border: 1px solid {glass_edge(60)};
                border-radius: {RADIUS_MD};
                selection-background-color: {t.SELECTION};
                selection-color: {t.TEXT};
                caretprecision: 0.5;
            }}
            QPlainTextEdit:focus, QTextEdit:focus {{
                border: 1px solid {t.ACCENT};
            }}

            /* ── Scrollbars ── */
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                border: none;
                margin: 2px;
                padding: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {hex_to_rgba(COLORS["scrollbar_handle"], 180)};
                min-height: 24px;
                border-radius: 5px;
                margin: 0;
                border: 2px solid transparent;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {hex_to_rgba(COLORS["scrollbar_hover"], 220)};
                border: 2px solid transparent;
            }}
            QScrollBar::handle:vertical:pressed {{
                background: {hex_to_rgba(COLORS["seafoam_dim"], 200)};
                border: 2px solid transparent;
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
                margin: 2px;
                padding: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {hex_to_rgba(COLORS["scrollbar_handle"], 180)};
                min-width: 24px;
                border-radius: 5px;
                margin: 0;
                border: 2px solid transparent;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {hex_to_rgba(COLORS["scrollbar_hover"], 220)};
                border: 2px solid transparent;
            }}
            QScrollBar::handle:horizontal:pressed {{
                background: {hex_to_rgba(COLORS["seafoam_dim"], 200)};
                border: 2px solid transparent;
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
                background: {glass_bg(100)};
                color: {t.TEXT};
                border: none;
                outline: none;
                show-decoration-selected: 0;
                border-radius: {RADIUS_MD};
            }}
            QTreeView::item {{
                padding: 2px 0;
                border: none;
                min-height: 22px;
                margin: 0;
                border-radius: {RADIUS_MD};
            }}
            QTreeView::item:hover {{
                background: {glass_bg(140)};
            }}
            QTreeView::item:selected {{
                background: {hex_to_rgba(COLORS["surface_selected"], 180)};
                color: {t.ACCENT};
                border: none;
            }}
            QTreeView::branch {{
                background: transparent;
                border: none;
            }}
            QTreeView::item:disabled {{
                color: {t.TEXT_MUTED};
            }}

            /* ── Line Edit ── */
            QLineEdit {{
                background: {glass_bg_dark(120)};
                color: {t.TEXT};
                border: 1px solid {glass_edge(60)};
                padding: 4px 8px;
                border-radius: {RADIUS_MD};
                selection-background-color: {t.ACCENT};
                selection-color: {t.BG};
                min-height: 24px;
            }}
            QLineEdit:focus {{
                border: 1px solid {t.ACCENT};
                background: {glass_bg_dark(150)};
                selection-background-color: {t.ACCENT_DIM};
            }}
            QLineEdit::placeholder {{
                color: {t.TEXT_MUTED};
            }}
            QLineEdit:disabled {{
                color: {t.TEXT_MUTED};
                background: {glass_bg_dark(60)};
            }}

            /* ── Buttons ── */
            QPushButton {{
                background: {glass_bg(140)};
                color: {t.TEXT_DIM};
                border: 1px solid {glass_edge(70)};
                padding: 4px 10px;
                border-radius: {RADIUS_MD};
                text-align: left;
            }}
            QPushButton:hover {{
                color: {t.ACCENT};
                background: {glass_bg(190)};
                border-color: {glass_edge(100)};
            }}
            QPushButton:pressed {{
                background: {glass_bg_dark(200)};
                border-color: {glass_edge(120)};
                color: {t.ACCENT};
            }}
            QPushButton:checked {{
                background: {hex_to_rgba(COLORS["seafoam_deep"], 180)};
                border-color: {glass_edge(120)};
                color: {t.ACCENT};
            }}
            QPushButton:disabled {{
                color: {t.TEXT_MUTED};
                background: {glass_bg_dark(80)};
                border-color: {COLORS["border_dim"]};
            }}

            /* ── Tab Widget ── */
            QTabWidget::pane {{
                background: {glass_bg(160)};
                border: 1px solid {glass_edge()};
                border-radius: {RADIUS_LG};
                top: -1px;
            }}
            QTabBar {{
                background: {glass_bg_dark(120)};
                border-radius: {RADIUS_LG};
            }}

            /* ── Tooltips ── */
            QToolTip {{
                background: {glass_bg(240)};
                color: {t.TEXT};
                border: 1px solid {glass_edge()};
                padding: 4px 8px;
                border-radius: {RADIUS_MD};
                opacity: 230;
            }}
            QToolTip::label {{
                background: transparent;
                border: none;
                padding: 0;
            }}

            /* ── Status Bar ── */
            QStatusBar {{
                background: {glass_bg(170)};
                color: {t.BG};
                border-top: 1px solid {glass_edge()};
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
                background: {glass_bg(60)};
                border: 1px solid {glass_edge()};
                border-radius: {RADIUS_LG};
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
                background: {glass_bg_dark(100)};
                border: 1px solid {glass_edge(50)};
                border-radius: 4px;
                text-align: center;
                color: {t.TEXT_DIM};
                min-height: 16px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS["seafoam_deep"]}, stop:1 {t.ACCENT});
                border-radius: 3px;
            }}
        """
