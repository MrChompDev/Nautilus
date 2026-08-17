"""
Surfline Theme - Deep Ocean Industrial
Dense, atmospheric, oceanic. Glassmorphism surfaces.
"""

try:
    from core import theme as _core_theme  # noqa: F401
    _HAS_CORE = True
except ImportError:
    _HAS_CORE = False

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

def _hex_to_rgba(h, a=255):
    v = h.lstrip("#")
    return f"rgba({int(v[0:2],16)},{int(v[2:4],16)},{int(v[4:6],16)},{a})"

def _glass_bg(a=180): return _hex_to_rgba(COLORS.get("bg_secondary", "#0E2238"), a)
def _glass_bg_dark(a=140): return _hex_to_rgba(COLORS.get("bg_primary", "#081626"), a)
def _glass_bg_heavy(a=220): return _hex_to_rgba(COLORS.get("bg_secondary", "#0E2238"), a)
def _glass_edge(a=48): return _hex_to_rgba(COLORS.get("biolum", "#00F2C2"), a)
def _glass_sheen(): return "rgba(238, 244, 248, 26)"

_R_SM = "8px"
_R_MD = "12px"
_R_LG = "18px"


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
        border: 1px solid {_glass_edge()};
        background: {_glass_bg(160)};
        border-radius: {_R_LG};
    }}

    QTabBar::tab {{
        background: {_glass_bg_dark(120)};
        color: {COLORS['text_secondary']};
        padding: 4px 12px;
        margin-right: 1px;
        border: 1px solid transparent;
        border-bottom: 2px solid transparent;
        border-radius: {_R_SM};
        min-width: 80px;
        max-width: 200px;
        height: 28px;
    }}

    QTabBar::tab:selected {{
        background: {_glass_bg(180)};
        color: {COLORS['accent']};
        border-bottom: 2px solid {COLORS['accent']};
    }}

    QTabBar::tab:hover:!selected {{
        background: {_glass_bg(150)};
        color: {COLORS['text_primary']};
    }}

    QTabBar::close-button {{
        image: none;
        subcontrol-position: right;
        padding: 2px;
        border-radius: 8px;
    }}

    QTabBar::close-button:hover {{
        background: {COLORS['error']};
    }}

    QLineEdit {{
        background: {_glass_bg_dark(120)};
        color: {COLORS['text_primary']};
        border: 1px solid {_glass_edge(60)};
        border-radius: {_R_SM};
        padding: 3px 8px;
        selection-background-color: {COLORS['selection']};
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
    }}

    QLineEdit:focus {{
        border: 1px solid {COLORS['accent']};
    }}

    QPushButton {{
        background: {_glass_bg(140)};
        color: {COLORS['text_primary']};
        border: 1px solid {_glass_edge(70)};
        border-radius: {_R_SM};
        padding: 3px 10px;
        min-width: 24px;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background: {_glass_bg(190)};
        border-color: {_glass_edge(100)};
    }}

    QPushButton:pressed {{
        background: {_glass_bg_dark(200)};
        border-color: {_glass_edge(120)};
        color: {COLORS['accent']};
    }}

    QToolButton {{
        background: transparent;
        color: {COLORS['text_secondary']};
        border: none;
        border-radius: {_R_SM};
        padding: 2px 6px;
        font-size: {FONTS['size_lg']}px;
    }}

    QToolButton:hover {{
        color: {COLORS['accent']};
        background: {_glass_bg(130)};
    }}

    QToolButton:pressed {{
        color: {COLORS['accent']};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {_hex_to_rgba(COLORS['scrollbar_handle'], 180)};
        min-height: 20px;
        border-radius: 5px;
        border: 2px solid transparent;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {_hex_to_rgba(COLORS['accent_darker'], 220)};
        border: 2px solid transparent;
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal {{
        background: {_hex_to_rgba(COLORS['scrollbar_handle'], 180)};
        min-width: 20px;
        border-radius: 5px;
        border: 2px solid transparent;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {_hex_to_rgba(COLORS['accent_darker'], 220)};
        border: 2px solid transparent;
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QMenu {{
        background: {_glass_bg_heavy(230)};
        color: {COLORS['text_primary']};
        border: 1px solid {_glass_edge()};
        border-radius: {_R_MD};
        padding: 4px 0px;
    }}

    QMenu::item {{
        padding: 4px 20px;
    }}

    QMenu::item:selected {{
        background: {_hex_to_rgba(COLORS['accent_darker'], 180)};
        color: {COLORS['accent']};
    }}

    QMenu::separator {{
        height: 1px;
        background: {_glass_edge()};
        margin: 2px 8px;
    }}

    QSplitter::handle {{
        background: {_glass_edge(40)};
    }}

    QSplitter::handle:horizontal {{
        width: 3px;
    }}

    QSplitter::handle:vertical {{
        height: 3px;
    }}

    QLabel {{
        color: {COLORS['text_primary']};
    }}

    QComboBox {{
        background: {_glass_bg_dark(130)};
        color: {COLORS['text_primary']};
        border: 1px solid {_glass_edge(60)};
        border-radius: {_R_SM};
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
        background: {_glass_bg_heavy(240)};
        color: {COLORS['text_primary']};
        border: 1px solid {_glass_edge()};
        border-radius: {_R_MD};
        selection-background-color: {_hex_to_rgba(COLORS['accent_darker'], 180)};
    }}

    QStatusBar {{
        background: {_glass_bg(170)};
        color: {COLORS['text_secondary']};
        border-top: 1px solid {_glass_edge()};
        font-size: {FONTS['size_sm']}px;
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
    }}

    QProgressBar {{
        background: {_glass_bg_dark(100)};
        border: 1px solid {_glass_edge(50)};
        border-radius: 4px;
        text-align: center;
        color: {COLORS['text_primary']};
        height: 4px;
    }}

    QProgressBar::chunk {{
        background: {COLORS['accent']};
        border-radius: 3px;
    }}

    QToolTip {{
        background: {_glass_bg_heavy(240)};
        color: {COLORS['text_primary']};
        border: 1px solid {_glass_edge()};
        border-radius: {_R_SM};
        padding: 4px;
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
    }}

    QTextEdit {{
        background: {_hex_to_rgba(COLORS['terminal_bg'], 200)};
        color: {COLORS['terminal_text']};
        border: 1px solid {_glass_edge(60)};
        border-radius: {_R_MD};
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
        padding: 4px;
        selection-background-color: {COLORS['selection']};
    }}
    """
