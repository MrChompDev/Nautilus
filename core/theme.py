"""
Nautilus OS - Centralized Design Token System
Glassmorphism aesthetic: semi-transparent glass surfaces, rounded corners,
subtle edge highlights, oceanic blue palette.

Token Map (per PRD):
  Base Background  #081626 -> Abyss Navy  (root windows, viewports)
  Surface          #0E2238 -> Slate Navy  (sidebars, toolbars, panels)
  Primary Accent   #00F2C2 -> Seafoam     (carets, focus, active tabs)
  Alert/Warning    #FF7F50 -> Coral       (errors, breakpoints)
  Secondary Text   #EEF4F8 -> HD White    (mono fonts, labels)
"""

from PySide6.QtGui import QColor, QPalette

from core.logger import get_logger

_log = get_logger("THEME")
_log.info("Theme system initialized")

# ═══════════════════════════════════════════════════════════════
#  MASTER COLOR TOKENS
# ═══════════════════════════════════════════════════════════════

COLORS = {
    # -- Base Canvas --
    "abyss_navy":      "#081626",   # Root backgrounds, viewports
    "slate_navy":      "#0E2238",   # Sidebars, toolbars, inactive panels
    "deep_navy":       "#050D14",   # Deepest backgrounds (terminals, editors)
    "void_black":      "#02060A",   # Maximum darkness (overlays, focus mode)

    # -- Accents --
    "seafoam":         "#00F2C2",   # Primary accent -- carets, focus, active borders
    "seafoam_dim":     "#00C9A0",   # Muted accent for hover states
    "seafoam_glow":    "#00F2C240", # Glow / selection overlay
    "seafoam_deep":    "#004D40",   # Deep accent for pressed states

    # -- Alert & Status --
    "coral":           "#FF7F50",   # Errors, warnings, breakpoints
    "coral_dim":       "#CC6640",   # Muted warning
    "amber":           "#FFA502",   # Caution / medium alerts
    "emerald":         "#00C853",   # Success states

    # -- Text --
    "hd_white":        "#EEF4F8",   # Primary text, mono fonts
    "text_secondary":  "#8BA4B8",   # Secondary labels
    "text_muted":      "#506070",   # Muted / disabled text
    "text_bright":     "#FFFFFF",   # Peak brightness (headings, selection)

    # -- Refined borders & surfaces --
    "border":          "#173250",   # Slightly refined standard borders
    "border_active":   "#00F2C2",   # Active / focused border
    "border_dim":      "#0A1A2A",   # Subtle dividers

    # -- Enhanced interactive surfaces --
    "surface_hover":   "#15304A",   # Subtly refined hover state for panels
    "surface_pressed": "#0C1520",   # Refined pressed state
    "surface_selected":"#1E3A5F",   # Refined selected item bg

    # -- Terminal-Specific --
    "terminal_bg":     "#030810",   # Terminal background
    "terminal_fg":     "#00F2C2",   # Terminal foreground
    "terminal_dim":    "#007A6640", # Terminal dim overlay

    # -- Scrollbar --
    "scrollbar_bg":    "#050D14",
    "scrollbar_handle": "#1A3352",
    "scrollbar_hover":  "#254565",

    # -- Tabs --
    "tab_active":      "#0E2238",
    "tab_inactive":    "#050D14",
    "tab_hover":       "#0A1628",
}


# ═══════════════════════════════════════════════════════════════
#  TYPOGRAPHY
# ═══════════════════════════════════════════════════════════════

FONTS = {
    "mono": "JetBrains Mono",
    "mono_fallback": "Consolas",
    "mono_fallback2": "Fira Code",
    "ui": "Segoe UI",
    "size_xs": 10,
    "size_sm": 11,
    "size_md": 12,
    "size_lg": 13,
    "size_xl": 14,
    "size_xxl": 16,
    "size_title": 20,
}


# ═══════════════════════════════════════════════════════════════
#  SPACING & GEOMETRY
# ═══════════════════════════════════════════════════════════════

SPACING = {
    "xs": 2,
    "sm": 4,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "xxl": 24,
    "xxxl": 32,
}

# ── Border Radius Tokens ──
BORDER_RADIUS = "12px"
RADIUS_SM = "8px"
RADIUS_MD = "12px"
RADIUS_LG = "18px"
RADIUS_XL = "24px"


# ═══════════════════════════════════════════════════════════════
#  QCOLOR HELPERS
# ═══════════════════════════════════════════════════════════════

def qcolor(hex_str: str) -> QColor:
    """Convert hex string to QColor."""
    return QColor(hex_str)


def hex_to_rgba(hex_str: str, alpha: int = 255) -> str:
    """Convert hex to rgba() CSS string."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ═══════════════════════════════════════════════════════════════
#  GLASS SURFACE HELPERS
# ═══════════════════════════════════════════════════════════════

def glass_bg(alpha: int = 180) -> str:
    """Translucent panel background -- the wallpaper glows through."""
    return hex_to_rgba(COLORS["slate_navy"], alpha)


def glass_bg_dark(alpha: int = 140) -> str:
    """Darker translucent chip (metrics, date, buttons)."""
    return hex_to_rgba(COLORS["deep_navy"], alpha)


def glass_bg_heavy(alpha: int = 220) -> str:
    """Heavier glass for content areas needing more contrast."""
    return hex_to_rgba(COLORS["slate_navy"], alpha)


def glass_edge(alpha: int = 48) -> str:
    """Subtle seafoam edge for glass panels."""
    return hex_to_rgba(COLORS["seafoam"], alpha)


def glass_sheen() -> str:
    """Faint white sheen for the glass highlight line."""
    return "rgba(238, 244, 248, 26)"


def glass_shadow() -> str:
    """Subtle dark outer glow for elevated glass surfaces."""
    return hex_to_rgba(COLORS["void_black"], 80)


def glass_card_style(radius: int = 18) -> str:
    """Complete 3-part glass QSS block for card surfaces."""
    return (
        f"background: {glass_bg(185)};"
        f"border: 1px solid {glass_edge()};"
        f"border-top: 1px solid {glass_sheen()};"
        f"border-radius: {radius}px;"
    )


def glass_panel_style(radius: int = 18) -> str:
    """Glass QSS block for sidebar/panel surfaces (slightly heavier)."""
    return (
        f"background: {glass_bg_heavy(210)};"
        f"border: 1px solid {glass_edge()};"
        f"border-top: 1px solid {glass_sheen()};"
        f"border-radius: {radius}px;"
    )


def glass_button_style(variant: str = "secondary") -> str:
    """Glass button QSS block. Variants: primary, secondary, danger."""
    if variant == "primary":
        bg = hex_to_rgba(COLORS["seafoam_deep"], 160)
        border = hex_to_rgba(COLORS["seafoam"], 120)
        text = COLORS["seafoam"]
        hover_bg = hex_to_rgba(COLORS["seafoam_deep"], 210)
        press_bg = hex_to_rgba(COLORS["seafoam_deep"], 240)
    elif variant == "danger":
        bg = hex_to_rgba(COLORS["coral_dim"], 140)
        border = hex_to_rgba(COLORS["coral"], 100)
        text = COLORS["coral"]
        hover_bg = hex_to_rgba(COLORS["coral_dim"], 200)
        press_bg = hex_to_rgba(COLORS["coral_dim"], 230)
    else:
        bg = glass_bg(140)
        border = glass_edge(70)
        text = COLORS["hd_white"]
        hover_bg = glass_bg(190)
        press_bg = glass_bg_dark(200)

    return f"""
        QPushButton {{
            background: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: {RADIUS_SM};
            padding: 6px 16px;
            min-height: 22px;
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_sm']}px;
        }}
        QPushButton:hover {{
            background: {hover_bg};
            border: 1px solid {glass_edge(80)};
        }}
        QPushButton:pressed {{
            background: {press_bg};
            border: 1px solid {glass_edge(100)};
        }}
        QPushButton:disabled {{
            background: {glass_bg_dark(80)};
            color: {COLORS['text_muted']};
            border: 1px solid {COLORS['border_dim']};
        }}
    """


# ═══════════════════════════════════════════════════════════════
#  GLOBAL APPLICATION PALETTE
# ═══════════════════════════════════════════════════════════════

def create_nautilus_palette() -> QPalette:
    """Build a QPalette from Nautilus tokens."""
    p = QPalette()

    # Window / Background
    p.setColor(QPalette.Window,          qcolor(COLORS["abyss_navy"]))
    p.setColor(QPalette.WindowText,      qcolor(COLORS["hd_white"]))
    p.setColor(QPalette.Base,            qcolor(COLORS["deep_navy"]))
    p.setColor(QPalette.AlternateBase,   qcolor(COLORS["slate_navy"]))
    p.setColor(QPalette.Text,            qcolor(COLORS["hd_white"]))

    # Buttons
    p.setColor(QPalette.Button,          qcolor(COLORS["slate_navy"]))
    p.setColor(QPalette.ButtonText,      qcolor(COLORS["hd_white"]))

    # Highlights
    p.setColor(QPalette.Highlight,       qcolor(COLORS["seafoam"]))
    p.setColor(QPalette.HighlightedText, qcolor(COLORS["void_black"]))

    # Disabled
    p.setColor(QPalette.Disabled, QPalette.WindowText, qcolor(COLORS["text_muted"]))
    p.setColor(QPalette.Disabled, QPalette.Text,        qcolor(COLORS["text_muted"]))
    p.setColor(QPalette.Disabled, QPalette.ButtonText,  qcolor(COLORS["text_muted"]))

    # Tooltips
    p.setColor(QPalette.ToolTipBase,     qcolor(COLORS["slate_navy"]))
    p.setColor(QPalette.ToolTipText,     qcolor(COLORS["hd_white"]))

    # Links
    p.setColor(QPalette.Link,            qcolor(COLORS["seafoam"]))
    p.setColor(QPalette.LinkVisited,     qcolor(COLORS["seafoam_dim"]))

    return p


# ═══════════════════════════════════════════════════════════════
#  GLOBAL STYLESHEET
# ═══════════════════════════════════════════════════════════════

def get_global_stylesheet() -> str:
    """Generate the master Nautilus OS glassmorphism stylesheet.

    All elements enforce:
      - Rounded corners (12px default)
      - Semi-transparent glass surfaces
      - Subtle seafoam edge highlights
      - Oceanic blue palette
    """
    c = COLORS
    f = FONTS

    return f"""
    /* ======================================================
       NAUTILUS OS -- GLOBAL STYLESHEET v2.0
       Glassmorphism design language
       ====================================================== */

    /* -- Root Reset -- */
    * {{
        font-family: "{f['ui']}", "{f['mono']}", "{f['mono_fallback']}", "{f['mono_fallback2']}", monospace;
        font-size: {f['size_md']}px;
        border-radius: {BORDER_RADIUS};
        outline: none;
    }}

    /* -- Main Window -- */
    QMainWindow {{
        background-color: {c['abyss_navy']};
        border: none;
    }}

    QMainWindow::separator {{
        background-color: {c['border']};
        width: 2px;
        height: 2px;
        border-radius: 1px;
    }}

    /* -- Generic Widget -- */
    QWidget {{
        background-color: transparent;
        color: {c['hd_white']};
        border: none;
    }}

    /* -- Menu Bar -- */
    QMenuBar {{
        background: {glass_bg(190)};
        color: {c['hd_white']};
        border-bottom: 1px solid {glass_edge()};
        padding: 2px 0;
        font-family: "{f['ui']}";
        font-size: {f['size_sm']}px;
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 4px 12px;
        border: 1px solid transparent;
        border-radius: {RADIUS_SM};
    }}

    QMenuBar::item:selected {{
        background: {glass_bg(160)};
        border-color: {glass_edge()};
    }}

    QMenuBar::item:pressed {{
        background: {hex_to_rgba(c['seafoam_deep'], 180)};
        color: {c['seafoam']};
    }}

    /* -- Menus -- */
    QMenu {{
        background: {glass_bg_heavy(230)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge()};
        border-radius: {RADIUS_MD};
        padding: 6px 0;
        font-family: "{f['ui']}";
    }}

    QMenu::item {{
        padding: 6px 28px 6px 14px;
        border: none;
        border-radius: 0px;
    }}

    QMenu::item:selected {{
        background: {hex_to_rgba(c['seafoam_deep'], 180)};
        color: {c['seafoam']};
    }}

    QMenu::item:disabled {{
        color: {c['text_muted']};
    }}

    QMenu::separator {{
        height: 1px;
        background: {glass_edge()};
        margin: 4px 12px;
    }}

    QMenu::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 3px;
    }}

    /* -- Tab Widget -- */
    QTabWidget::pane {{
        background: {glass_bg(160)};
        border: 1px solid {glass_edge()};
        border-radius: {RADIUS_LG};
        top: -1px;
    }}

    QTabBar::tab {{
        background: {glass_bg_dark(120)};
        color: {c['text_secondary']};
        padding: 6px 16px;
        margin-right: 2px;
        border: 1px solid transparent;
        border-bottom: 2px solid transparent;
        border-radius: {RADIUS_SM};
        min-width: 90px;
        max-width: 200px;
        height: 30px;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
    }}

    QTabBar::tab:selected {{
        background: {glass_bg(180)};
        color: {c['seafoam']};
        border-bottom: 2px solid {c['seafoam']};
        border-color: {glass_edge()};
    }}

    QTabBar::tab:hover:!selected {{
        background: {glass_bg(150)};
        color: {c['hd_white']};
        border-color: {glass_edge(30)};
    }}

    QTabBar::close-button {{
        subcontrol-position: right;
        padding: 2px;
        border-radius: 8px;
    }}

    QTabBar::close-button:hover {{
        background-color: {c['coral']};
    }}

    /* -- Buttons -- */
    QPushButton {{
        background: {glass_bg(140)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge(70)};
        border-radius: {RADIUS_SM};
        padding: 6px 16px;
        min-width: 28px;
        min-height: 22px;
        font-family: "{f['ui']}";
        font-size: {f['size_sm']}px;
    }}

    QPushButton:hover {{
        background: {glass_bg(190)};
        border-color: {glass_edge(100)};
        color: {c['seafoam']};
    }}

    QPushButton:pressed {{
        background: {glass_bg_dark(200)};
        border-color: {glass_edge(120)};
        color: {c['seafoam']};
    }}

    QPushButton:disabled {{
        color: {c['text_muted']};
        background: {glass_bg_dark(80)};
        border-color: {c['border_dim']};
    }}

    QPushButton:checked {{
        background: {hex_to_rgba(c['seafoam_deep'], 180)};
        border-color: {glass_edge(120)};
        color: {c['seafoam']};
    }}

    /* -- Tool Buttons -- */
    QToolButton {{
        background: transparent;
        color: {c['text_secondary']};
        border: 1px solid transparent;
        border-radius: {RADIUS_SM};
        padding: 4px 8px;
        font-family: "{f['ui']}";
    }}

    QToolButton:hover {{
        color: {c['seafoam']};
        background: {glass_bg(130)};
        border-color: {glass_edge(50)};
    }}

    QToolButton:pressed {{
        color: {c['seafoam']};
        background: {hex_to_rgba(c['seafoam_deep'], 160)};
    }}

    /* -- Line Edit / Text Input -- */
    QLineEdit {{
        background: {glass_bg_dark(120)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge(60)};
        border-radius: {RADIUS_SM};
        padding: 5px 12px;
        selection-background-color: {c['seafoam_glow']};
        selection-color: {c['hd_white']};
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
        min-height: 24px;
    }}

    QLineEdit:focus {{
        border: 1px solid {c['seafoam']};
        background: {glass_bg_dark(150)};
    }}

    QLineEdit::placeholder {{
        color: {c['text_muted']};
    }}

    QLineEdit:disabled {{
        color: {c['text_muted']};
        background: {glass_bg_dark(60)};
    }}

    /* -- Text Edit / Plain Text -- */
    QTextEdit, QPlainTextEdit {{
        background: {hex_to_rgba(c['terminal_bg'], 200)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge(60)};
        border-radius: {RADIUS_MD};
        font-family: "{f['mono']}", "{f['mono_fallback']}";
        font-size: {f['size_sm']}px;
        padding: 8px;
        selection-background-color: {c['seafoam_glow']};
        selection-color: {c['text_bright']};
    }}

    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {c['seafoam']};
    }}

    /* -- Tree View -- */
    QTreeView {{
        background: {glass_bg(100)};
        color: {c['hd_white']};
        border: none;
        outline: none;
        show-decoration-selected: 0;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
        border-radius: {RADIUS_MD};
    }}

    QTreeView::item {{
        padding: 4px 8px;
        border: none;
        border-radius: {RADIUS_SM};
        min-height: 24px;
    }}

    QTreeView::item:hover {{
        background: {glass_bg(140)};
    }}

    QTreeView::item:selected {{
        background: {hex_to_rgba(c['surface_selected'], 180)};
        color: {c['seafoam']};
    }}

    QTreeView::branch {{
        background: transparent;
        border: none;
    }}

    QTreeView::branch:has-children:!has-siblings:closed,
    QTreeView::branch:closed:has-children:has-siblings {{
        border-image: none;
    }}

    QTreeView::branch:open:has-children:!has-siblings,
    QTreeView::branch:open:has-children:has-siblings {{
        border-image: none;
    }}

    /* -- List View -- */
    QListView {{
        background: {glass_bg(100)};
        color: {c['hd_white']};
        border: none;
        outline: none;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
        border-radius: {RADIUS_MD};
    }}

    QListView::item {{
        padding: 4px 10px;
        border: none;
        border-radius: {RADIUS_SM};
    }}

    QListView::item:hover {{
        background: {glass_bg(140)};
    }}

    QListView::item:selected {{
        background: {hex_to_rgba(c['surface_selected'], 180)};
        color: {c['seafoam']};
    }}

    /* -- Table View -- */
    QTableView {{
        background: {glass_bg(100)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge()};
        border-radius: {RADIUS_MD};
        gridline-color: {c['border_dim']};
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
    }}

    QTableView::item {{
        padding: 5px 10px;
        border-radius: 0px;
    }}

    QTableView::item:hover {{
        background: {glass_bg(140)};
    }}

    QTableView::item:selected {{
        background: {hex_to_rgba(c['surface_selected'], 180)};
        color: {c['seafoam']};
    }}

    QHeaderView::section {{
        background: {glass_bg_dark(180)};
        color: {c['seafoam']};
        padding: 5px 10px;
        border: none;
        border-right: 1px solid {c['border_dim']};
        border-bottom: 2px solid {glass_edge()};
        border-radius: 0px;
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* -- Scrollbars -- */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {hex_to_rgba(c['scrollbar_handle'], 180)};
        min-height: 24px;
        border-radius: 5px;
        border: 2px solid transparent;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {hex_to_rgba(c['scrollbar_hover'], 220)};
        border: 2px solid transparent;
    }}

    QScrollBar::handle:vertical:pressed {{
        background: {hex_to_rgba(c['seafoam_dim'], 200)};
        border: 2px solid transparent;
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal {{
        background: {hex_to_rgba(c['scrollbar_handle'], 180)};
        min-width: 24px;
        border-radius: 5px;
        border: 2px solid transparent;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {hex_to_rgba(c['scrollbar_hover'], 220)};
        border: 2px solid transparent;
    }}

    QScrollBar::handle:horizontal:pressed {{
        background: {hex_to_rgba(c['seafoam_dim'], 200)};
        border: 2px solid transparent;
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* -- Splitter -- */
    QSplitter::handle {{
        background: {glass_edge(40)};
        border-radius: 1px;
    }}

    QSplitter::handle:horizontal {{
        width: 3px;
    }}

    QSplitter::handle:vertical {{
        height: 3px;
    }}

    QSplitter::handle:hover {{
        background: {c['seafoam_dim']};
    }}

    /* -- Status Bar -- */
    QStatusBar {{
        background: {glass_bg(170)};
        color: {c['text_secondary']};
        border-top: 1px solid {glass_edge()};
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}px;
        padding: 3px 10px;
    }}

    QStatusBar::item {{
        border: none;
        padding: 0 8px;
    }}

    /* -- Labels -- */
    QLabel {{
        background: transparent;
        border: none;
        color: {c['hd_white']};
        padding: 0;
    }}

    /* -- Group Box -- */
    QGroupBox {{
        background: {glass_bg(60)};
        border: 1px solid {glass_edge()};
        border-radius: {RADIUS_LG};
        margin-top: 16px;
        padding-top: 20px;
        padding-left: 8px;
        padding-right: 8px;
        padding-bottom: 8px;
        font-family: "{f['ui']}";
        font-weight: bold;
        color: {c['seafoam']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
        color: {c['seafoam']};
    }}

    /* -- Combo Box -- */
    QComboBox {{
        background: {glass_bg_dark(130)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge(60)};
        border-radius: {RADIUS_SM};
        padding: 5px 12px;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
        min-height: 24px;
    }}

    QComboBox:focus {{
        border: 1px solid {c['seafoam']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
        border-radius: 0px;
    }}

    QComboBox::down-arrow {{
        border: none;
    }}

    QComboBox QAbstractItemView {{
        background: {glass_bg_heavy(240)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge()};
        border-radius: {RADIUS_MD};
        selection-background-color: {hex_to_rgba(c['seafoam_deep'], 180)};
        selection-color: {c['seafoam']};
    }}

    /* -- Spin Box -- */
    QSpinBox, QDoubleSpinBox {{
        background: {glass_bg_dark(130)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge(60)};
        border-radius: {RADIUS_SM};
        padding: 5px 10px;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {c['seafoam']};
    }}

    /* -- Check Box / Radio -- */
    QCheckBox, QRadioButton {{
        color: {c['hd_white']};
        spacing: 8px;
        font-family: "{f['ui']}";
    }}

    QCheckBox::indicator, QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {glass_edge(80)};
        border-radius: 4px;
        background: {glass_bg_dark(120)};
    }}

    QCheckBox::indicator:checked {{
        background: {hex_to_rgba(c['seafoam_deep'], 200)};
        border-color: {c['seafoam']};
        border-radius: 4px;
    }}

    QRadioButton::indicator {{
        border-radius: 9px;
    }}

    QRadioButton::indicator:checked {{
        background: {hex_to_rgba(c['seafoam_deep'], 200)};
        border-color: {c['seafoam']};
        border-radius: 9px;
    }}

    /* -- Progress Bar -- */
    QProgressBar {{
        background: {glass_bg_dark(100)};
        border: 1px solid {glass_edge(50)};
        border-radius: 4px;
        text-align: center;
        color: {c['hd_white']};
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}px;
        height: 8px;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['seafoam_deep']}, stop:1 {c['seafoam']});
        border-radius: 3px;
    }}

    /* -- Tool Tips -- */
    QToolTip {{
        background: {glass_bg_heavy(240)};
        color: {c['hd_white']};
        border: 1px solid {glass_edge()};
        border-radius: {RADIUS_SM};
        padding: 6px 12px;
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}px;
    }}

    /* -- Dock Widget -- */
    QDockWidget {{
        titlebar-close-icon: none;
        titlebar-normal-icon: none;
    }}

    QDockWidget::title {{
        background: {glass_bg_dark(180)};
        padding: 5px 12px;
        border-bottom: 1px solid {glass_edge()};
        border-radius: 0px;
    }}

    /* -- Slider -- */
    QSlider::groove:horizontal {{
        background: {glass_bg_dark(120)};
        height: 6px;
        border: 1px solid {glass_edge(40)};
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background: {c['seafoam']};
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border: 2px solid {c['seafoam_dim']};
        border-radius: 8px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {c['seafoam_dim']};
        border-color: {c['seafoam']};
    }}

    QSlider::sub-page:horizontal {{
        background: {hex_to_rgba(c['seafoam_deep'], 200)};
        border-radius: 3px;
    }}

    /* -- Focus Indicator -- */
    *:focus {{
        outline: none;
    }}
    """
