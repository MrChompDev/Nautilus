"""
Surfline Theme - Deep Ocean Industrial
Dense, atmospheric, oceanic. Flat edges, no frills.
"""

COLORS = {
    "bg_primary": "#060E1A",
    "bg_secondary": "#0A1628",
    "bg_tertiary": "#0D1F35",
    "bg_elevated": "#112A45",
    "bg_input": "#081A2E",
    "accent": "#00F2C2",
    "accent_dim": "#00C9A0",
    "accent_darker": "#007A66",
    "accent_glow": "#00F2C230",
    "accent_deep": "#004D40",
    "text_primary": "#D8E2EC",
    "text_secondary": "#7A8FA0",
    "text_muted": "#4A5D6E",
    "text_bright": "#FFFFFF",
    "border": "#152D44",
    "border_active": "#00F2C2",
    "border_glow": "#00F2C218",
    "error": "#FF4757",
    "warning": "#FFA502",
    "success": "#00F2C2",
    "tab_active": "#0D1F35",
    "tab_inactive": "#050C14",
    "tab_hover": "#0A1628",
    "scrollbar_bg": "#050C14",
    "scrollbar_handle": "#152D44",
    "terminal_bg": "#030910",
    "terminal_text": "#00F2C2",
    "terminal_dim": "#007A6660",
    "selection": "#00F2C228",
    "ocean_deep": "#020810",
    "ocean_mid": "#061520",
    "ocean_surface": "#0A1E33",
    "ocean_light": "#122E48",
    "biolum": "#00F2C2",
    "biolum_dim": "#00F2C240",
    "reef_dark": "#0B1E2E",
    "reef_line": "#1A3A52",
}

SPACING = {
    "xs": 2,
    "sm": 4,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "xxl": 24,
}

FONTS = {
    "mono": "JetBrains Mono",
    "fallback_mono": "Consolas",
    "fallback_mono2": "Fira Code",
    "ui": "Segoe UI",
    "size_xs": 10,
    "size_sm": 11,
    "size_md": 12,
    "size_lg": 13,
    "size_xl": 14,
}

def get_stylesheet():
    return f"""
    * {{
        font-family: "{FONTS['ui']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_md']}px;
    }}

    QMainWindow {{
        background-color: {COLORS['bg_primary']};
    }}

    QWidget {{
        background-color: transparent;
        color: {COLORS['text_primary']};
    }}

    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        background: {COLORS['bg_primary']};
    }}

    QTabBar::tab {{
        background: {COLORS['tab_inactive']};
        color: {COLORS['text_secondary']};
        padding: 4px 12px;
        margin-right: 1px;
        border: none;
        border-bottom: 2px solid transparent;
        min-width: 80px;
        max-width: 200px;
        height: 28px;
    }}

    QTabBar::tab:selected {{
        background: {COLORS['tab_active']};
        color: {COLORS['accent']};
        border-bottom: 2px solid {COLORS['accent']};
    }}

    QTabBar::tab:hover:!selected {{
        background: {COLORS['tab_hover']};
        color: {COLORS['text_primary']};
    }}

    QTabBar::close-button {{
        image: none;
        subcontrol-position: right;
        padding: 2px;
    }}

    QTabBar::close-button:hover {{
        background: {COLORS['error']};
    }}

    QLineEdit {{
        background: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 3px 8px;
        selection-background-color: {COLORS['selection']};
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
    }}

    QLineEdit:focus {{
        border: 1px solid {COLORS['accent']};
    }}

    QPushButton {{
        background: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 3px 10px;
        min-width: 24px;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background: {COLORS['border']};
        border-color: {COLORS['accent_dim']};
    }}

    QPushButton:pressed {{
        background: {COLORS['accent_darker']};
        color: {COLORS['bg_primary']};
    }}

    QToolButton {{
        background: transparent;
        color: {COLORS['text_secondary']};
        border: none;
        padding: 2px 6px;
        font-size: {FONTS['size_lg']}px;
    }}

    QToolButton:hover {{
        color: {COLORS['accent']};
        background: {COLORS['bg_elevated']};
    }}

    QToolButton:pressed {{
        color: {COLORS['accent']};
    }}

    QScrollBar:vertical {{
        background: {COLORS['scrollbar_bg']};
        width: 6px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {COLORS['scrollbar_handle']};
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {COLORS['accent_darker']};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {COLORS['scrollbar_bg']};
        height: 6px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: {COLORS['scrollbar_handle']};
        min-width: 20px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {COLORS['accent_darker']};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QMenu {{
        background: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 2px 0px;
    }}

    QMenu::item {{
        padding: 4px 20px;
    }}

    QMenu::item:selected {{
        background: {COLORS['accent_darker']};
        color: {COLORS['text_primary']};
    }}

    QMenu::separator {{
        height: 1px;
        background: {COLORS['border']};
        margin: 2px 0px;
    }}

    QSplitter::handle {{
        background: {COLORS['border']};
    }}

    QSplitter::handle:horizontal {{
        width: 2px;
    }}

    QSplitter::handle:vertical {{
        height: 2px;
    }}

    QLabel {{
        color: {COLORS['text_primary']};
    }}

    QComboBox {{
        background: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 3px 8px;
    }}

    QComboBox:focus {{
        border: 1px solid {COLORS['accent']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 16px;
    }}

    QComboBox QAbstractItemView {{
        background: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        selection-background-color: {COLORS['accent_darker']};
    }}

    QStatusBar {{
        background: {COLORS['bg_secondary']};
        color: {COLORS['text_secondary']};
        border-top: 1px solid {COLORS['border']};
        font-size: {FONTS['size_sm']}px;
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
    }}

    QProgressBar {{
        background: {COLORS['bg_input']};
        border: none;
        text-align: center;
        color: {COLORS['text_primary']};
        height: 2px;
    }}

    QProgressBar::chunk {{
        background: {COLORS['accent']};
    }}

    QToolTip {{
        background: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['accent']};
        padding: 4px;
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
    }}

    QTextEdit {{
        background: {COLORS['terminal_bg']};
        color: {COLORS['terminal_text']};
        border: 1px solid {COLORS['border']};
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
        padding: 4px;
        selection-background-color: {COLORS['selection']};
    }}
    """
