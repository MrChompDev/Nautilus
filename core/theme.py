"""
Nautilus OS - Centralized Design Token System
Enforces 0px border-radius, futuristic cyber-terminal aesthetic with blue oceanic tones.

Token Map (per PRD):
  Base Background  #081626 → Abyss Navy  (root windows, viewports)
  Surface          #0E2238 → Slate Navy  (sidebars, toolbars, panels)
  Primary Accent   #00F2C2 → Seafoam     (carets, focus, active tabs)
  Alert/Warning    #FF7F50 → Coral       (errors, breakpoints)
  Secondary Text   #EEF4F8 → HD White    (mono fonts, labels)
"""

from PySide6.QtGui import QColor, QPalette

from core.logger import get_logger

_log = get_logger("THEME")
_log.info("Theme system initialized")

# ═══════════════════════════════════════════════════════════════
#  MASTER COLOR TOKENS
# ═══════════════════════════════════════════════════════════════

COLORS = {
    # ── Base Canvas ──
    "abyss_navy":      "#081626",   # Root backgrounds, viewports
    "slate_navy":      "#0E2238",   # Sidebars, toolbars, inactive panels
    "deep_navy":       "#050D14",   # Deepest backgrounds (terminals, editors)
    "void_black":      "#02060A",   # Maximum darkness (overlays, focus mode)

    # ── Accents ──
    "seafoam":         "#00F2C2",   # Primary accent — carets, focus, active borders
    "seafoam_dim":     "#00C9A0",   # Muted accent for hover states
    "seafoam_glow":    "#00F2C240", # Glow / selection overlay
    "seafoam_deep":    "#004D40",   # Deep accent for pressed states

    # ── Alert & Status ──
    "coral":           "#FF7F50",   # Errors, warnings, breakpoints
    "coral_dim":       "#CC6640",   # Muted warning
    "amber":           "#FFA502",   # Caution / medium alerts
    "emerald":         "#00C853",   # Success states

    # ── Text ──
    "hd_white":        "#EEF4F8",   # Primary text, mono fonts
    "text_secondary":  "#8BA4B8",   # Secondary labels
    "text_muted":      "#506070",   # Muted / disabled text
    "text_bright":     "#FFFFFF",   # Peak brightness (headings, selection)

    # ── Borders & Lines ──
    "border":          "#152D44",   # Standard borders
    "border_active":   "#00F2C2",   # Active / focused border
    "border_dim":      "#0A1A2A",   # Subtle dividers

    # ── Interactive Surfaces ──
    "surface_hover":   "#132A40",   # Hover state for panels
    "surface_pressed": "#0A1A2A",   # Pressed state
    "surface_selected":"#1A3352",   # Selected item bg

    # ── Terminal-Specific ──
    "terminal_bg":     "#030810",   # Terminal background
    "terminal_fg":     "#00F2C2",   # Terminal foreground
    "terminal_dim":    "#007A6640", # Terminal dim overlay

    # ── Scrollbar ──
    "scrollbar_bg":    "#050D14",
    "scrollbar_handle": "#1A3352",
    "scrollbar_hover":  "#254565",

    # ── Tabs ──
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

# Global rule: absolutely no border-radius anywhere
BORDER_RADIUS = "0px"


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
    """Generate the master Nautilus OS stylesheet.

    All elements enforce:
      - border-radius: 0px (strict zero-radius design)
      - Futuristic cyber-terminal aesthetic
      - Blue oceanic color palette
    """
    c = COLORS
    f = FONTS

    return f"""
    /* ══════════════════════════════════════════════════════
       NAUTILUS OS — GLOBAL STYLESHEET v1.0
       Zero-radius cyber-terminal design language
       ══════════════════════════════════════════════════════ */

    /* ── Root Reset ── */
    * {{
        font-family: "{f['ui']}", "{f['mono']}", "{f['mono_fallback']}", "{f['mono_fallback2']}", monospace;
        font-size: {f['size_md']}px;
        border-radius: {BORDER_RADIUS};
        outline: none;
    }}

    /* ── Main Window ── */
    QMainWindow {{
        background-color: {c['abyss_navy']};
        border: none;
    }}

    QMainWindow::separator {{
        background-color: {c['border']};
        width: 1px;
        height: 1px;
    }}

    /* ── Generic Widget ── */
    QWidget {{
        background-color: transparent;
        color: {c['hd_white']};
        border: none;
    }}

    /* ── Menu Bar ── */
    QMenuBar {{
        background-color: {c['void_black']};
        color: {c['hd_white']};
        border-bottom: 1px solid {c['border']};
        padding: 2px 0;
        font-family: "{f['ui']}";
        font-size: {f['size_sm']}px;
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 4px 12px;
        border: 1px solid transparent;
    }}

    QMenuBar::item:selected {{
        background-color: {c['slate_navy']};
        border-color: {c['border']};
    }}

    QMenuBar::item:pressed {{
        background-color: {c['seafoam_deep']};
        color: {c['seafoam']};
    }}

    /* ── Menus ── */
    QMenu {{
        background-color: {c['slate_navy']};
        color: {c['hd_white']};
        border: 1px solid {c['border']};
        padding: 4px 0;
        font-family: "{f['ui']}";
    }}

    QMenu::item {{
        padding: 5px 28px 5px 12px;
        border: none;
    }}

    QMenu::item:selected {{
        background-color: {c['seafoam_deep']};
        color: {c['seafoam']};
    }}

    QMenu::item:disabled {{
        color: {c['text_muted']};
    }}

    QMenu::separator {{
        height: 1px;
        background: {c['border']};
        margin: 4px 10px;
    }}

    QMenu::indicator {{
        width: 14px;
        height: 14px;
    }}

    /* ── Tab Widget ── */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        background-color: {c['abyss_navy']};
        top: -1px;
    }}

    QTabBar::tab {{
        background-color: {c['tab_inactive']};
        color: {c['text_secondary']};
        padding: 5px 14px;
        margin-right: 0px;
        border: none;
        border-bottom: 2px solid transparent;
        min-width: 90px;
        max-width: 200px;
        height: 28px;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
    }}

    QTabBar::tab:selected {{
        background-color: {c['tab_active']};
        color: {c['seafoam']};
        border-bottom: 2px solid {c['seafoam']};
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {c['tab_hover']};
        color: {c['hd_white']};
    }}

    QTabBar::close-button {{
        subcontrol-position: right;
        padding: 2px;
    }}

    QTabBar::close-button:hover {{
        background-color: {c['coral']};
    }}

    /* ── Buttons ── */
    QPushButton {{
        background-color: {c['slate_navy']};
        color: {c['hd_white']};
        border: 1px solid {c['border']};
        padding: 5px 14px;
        min-width: 28px;
        min-height: 22px;
        font-family: "{f['ui']}";
        font-size: {f['size_sm']}px;
    }}

    QPushButton:hover {{
        background-color: {c['surface_hover']};
        border-color: {c['seafoam_dim']};
        color: {c['seafoam']};
    }}

    QPushButton:pressed {{
        background-color: {c['seafoam_deep']};
        border-color: {c['seafoam']};
        color: {c['seafoam']};
    }}

    QPushButton:disabled {{
        color: {c['text_muted']};
        background-color: {c['deep_navy']};
        border-color: {c['border_dim']};
    }}

    QPushButton:checked {{
        background-color: {c['seafoam_deep']};
        border-color: {c['seafoam']};
        color: {c['seafoam']};
    }}

    /* ── Tool Buttons ── */
    QToolButton {{
        background-color: transparent;
        color: {c['text_secondary']};
        border: 1px solid transparent;
        padding: 3px 8px;
        font-family: "{f['ui']}";
    }}

    QToolButton:hover {{
        color: {c['seafoam']};
        background-color: {c['surface_hover']};
        border-color: {c['border']};
    }}

    QToolButton:pressed {{
        color: {c['seafoam']};
        background-color: {c['seafoam_deep']};
    }}

    /* ── Line Edit / Text Input ── */
    QLineEdit {{
        background-color: {c['deep_navy']};
        color: {c['hd_white']};
        border: 1px solid {c['border']};
        padding: 4px 10px;
        selection-background-color: {c['seafoam_glow']};
        selection-color: {c['hd_white']};
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
        min-height: 24px;
    }}

    QLineEdit:focus {{
        border: 1px solid {c['seafoam']};
        background-color: {c['void_black']};
    }}

    QLineEdit::placeholder {{
        color: {c['text_muted']};
    }}

    QLineEdit:disabled {{
        color: {c['text_muted']};
        background-color: {c['abyss_navy']};
    }}

    /* ── Text Edit / Plain Text ── */
    QTextEdit, QPlainTextEdit {{
        background-color: {c['terminal_bg']};
        color: {c['hd_white']};
        border: 1px solid {c['border']};
        font-family: "{f['mono']}", "{f['mono_fallback']}";
        font-size: {f['size_sm']}px;
        padding: 6px;
        selection-background-color: {c['seafoam_glow']};
        selection-color: {c['text_bright']};
    }}

    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {c['seafoam']};
    }}

    /* ── Tree View ── */
    QTreeView {{
        background-color: {c['slate_navy']};
        color: {c['hd_white']};
        border: none;
        outline: none;
        show-decoration-selected: 0;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
    }}

    QTreeView::item {{
        padding: 3px 6px;
        border: none;
        min-height: 22px;
    }}

    QTreeView::item:hover {{
        background-color: {c['surface_hover']};
    }}

    QTreeView::item:selected {{
        background-color: {c['surface_selected']};
        color: {c['seafoam']};
    }}

    QTreeView::branch {{
        background-color: {c['slate_navy']};
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

    /* ── List View ── */
    QListView {{
        background-color: {c['slate_navy']};
        color: {c['hd_white']};
        border: none;
        outline: none;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
    }}

    QListView::item {{
        padding: 3px 8px;
        border: none;
    }}

    QListView::item:hover {{
        background-color: {c['surface_hover']};
    }}

    QListView::item:selected {{
        background-color: {c['surface_selected']};
        color: {c['seafoam']};
    }}

    /* ── Table View ── */
    QTableView {{
        background-color: {c['slate_navy']};
        color: {c['hd_white']};
        border: 1px solid {c['border']};
        gridline-color: {c['border_dim']};
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
    }}

    QTableView::item {{
        padding: 4px 8px;
    }}

    QTableView::item:hover {{
        background-color: {c['surface_hover']};
    }}

    QTableView::item:selected {{
        background-color: {c['surface_selected']};
        color: {c['seafoam']};
    }}

    QHeaderView::section {{
        background-color: {c['void_black']};
        color: {c['seafoam']};
        padding: 4px 8px;
        border: none;
        border-right: 1px solid {c['border_dim']};
        border-bottom: 2px solid {c['border']};
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* ── Scrollbars ── */
    QScrollBar:vertical {{
        background-color: {c['scrollbar_bg']};
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c['scrollbar_handle']};
        min-height: 24px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c['scrollbar_hover']};
    }}

    QScrollBar::handle:vertical:pressed {{
        background-color: {c['seafoam_dim']};
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
        background-color: {c['scrollbar_bg']};
        height: 8px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {c['scrollbar_handle']};
        min-width: 24px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {c['scrollbar_hover']};
    }}

    QScrollBar::handle:horizontal:pressed {{
        background-color: {c['seafoam_dim']};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* ── Splitter ── */
    QSplitter::handle {{
        background-color: {c['border']};
    }}

    QSplitter::handle:horizontal {{
        width: 2px;
    }}

    QSplitter::handle:vertical {{
        height: 2px;
    }}

    QSplitter::handle:hover {{
        background-color: {c['seafoam_dim']};
    }}

    /* ── Status Bar ── */
    QStatusBar {{
        background-color: {c['slate_navy']};
        color: {c['text_secondary']};
        border-top: 1px solid {c['border']};
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}px;
        padding: 2px 8px;
    }}

    QStatusBar::item {{
        border: none;
        padding: 0 8px;
    }}

    /* ── Labels ── */
    QLabel {{
        background: transparent;
        border: none;
        color: {c['hd_white']};
        padding: 0;
    }}

    /* ── Group Box ── */
    QGroupBox {{
        border: 1px solid {c['border']};
        margin-top: 14px;
        padding-top: 18px;
        font-family: "{f['ui']}";
        font-weight: bold;
        color: {c['seafoam']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
        color: {c['seafoam']};
    }}

    /* ── Combo Box ── */
    QComboBox {{
        background-color: {c['deep_navy']};
        color: {c['hd_white']};
        border: 1px solid {c['border']};
        padding: 4px 10px;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
        min-height: 24px;
    }}

    QComboBox:focus {{
        border: 1px solid {c['seafoam']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox::down-arrow {{
        border: none;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c['slate_navy']};
        color: {c['hd_white']};
        border: 1px solid {c['border']};
        selection-background-color: {c['seafoam_deep']};
        selection-color: {c['seafoam']};
    }}

    /* ── Spin Box ── */
    QSpinBox, QDoubleSpinBox {{
        background-color: {c['deep_navy']};
        color: {c['hd_white']};
        border: 1px solid {c['border']};
        padding: 4px 8px;
        font-family: "{f['mono']}";
        font-size: {f['size_sm']}px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {c['seafoam']};
    }}

    /* ── Check Box / Radio ── */
    QCheckBox, QRadioButton {{
        color: {c['hd_white']};
        spacing: 8px;
        font-family: "{f['ui']}";
    }}

    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {c['border']};
        background-color: {c['deep_navy']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c['seafoam_deep']};
        border-color: {c['seafoam']};
    }}

    QRadioButton::indicator:checked {{
        background-color: {c['seafoam_deep']};
        border-color: {c['seafoam']};
    }}

    /* ── Progress Bar ── */
    QProgressBar {{
        background-color: {c['deep_navy']};
        border: 1px solid {c['border']};
        text-align: center;
        color: {c['hd_white']};
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}px;
        height: 6px;
    }}

    QProgressBar::chunk {{
        background-color: {c['seafoam']};
    }}

    /* ── Tool Tips ── */
    QToolTip {{
        background-color: {c['slate_navy']};
        color: {c['hd_white']};
        border: 1px solid {c['seafoam']};
        padding: 6px 10px;
        font-family: "{f['mono']}";
        font-size: {f['size_xs']}px;
    }}

    /* ── Dock Widget ── */
    QDockWidget {{
        titlebar-close-icon: none;
        titlebar-normal-icon: none;
    }}

    QDockWidget::title {{
        background-color: {c['void_black']};
        padding: 4px 10px;
        border-bottom: 1px solid {c['border']};
    }}

    /* ── Slider ── */
    QSlider::groove:horizontal {{
        background: {c['deep_navy']};
        height: 4px;
        border: 1px solid {c['border']};
    }}

    QSlider::handle:horizontal {{
        background: {c['seafoam']};
        width: 14px;
        height: 14px;
        margin: -6px 0;
        border: 1px solid {c['seafoam_dim']};
    }}

    QSlider::handle:horizontal:hover {{
        background: {c['seafoam_dim']};
        border-color: {c['seafoam']};
    }}

    QSlider::sub-page:horizontal {{
        background: {c['seafoam_deep']};
    }}

    /* ── Cyber Terminal Scanlines Effect ── */
    QMainWindow::backdrop {{
        background-color: {c['abyss_navy']};
    }}

    /* ── Focus Indicator ── */
    *:focus {{
        outline: none;
    }}
    """
