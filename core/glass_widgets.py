"""
Nautilus OS -- Reusable Glassmorphism Widgets

Drop-in replacements for standard Qt widgets with glass-surface styling.
Import these in app code instead of building glass styles inline.

Usage:
    from core.glass_widgets import GlassButton, GlassPanel, GlassCard
"""

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.theme import (
    COLORS,
    FONTS,
    RADIUS_SM,
    glass_bg,
    glass_bg_dark,
    glass_bg_heavy,
    glass_edge,
    glass_sheen,
    hex_to_rgba,
)

# ═══════════════════════════════════════════════════════════════
#  GlassButton
# ═══════════════════════════════════════════════════════════════

class GlassButton(QPushButton):
    """A modern glassmorphism button with variant support.

    Variants: 'primary' (seafoam accent), 'secondary' (translucent),
              'danger' (coral accent).
    """

    def __init__(
        self,
        text: str = "",
        variant: str = "secondary",
        icon=None,
        parent=None,
    ):
        super().__init__(text, parent)
        self._variant = variant
        if icon is not None:
            self.setIcon(icon)
        self._apply_style()

    def _apply_style(self):
        v = self._variant
        c = COLORS
        if v == "primary":
            bg = hex_to_rgba(c["seafoam_deep"], 160)
            border = hex_to_rgba(c["seafoam"], 120)
            text = c["seafoam"]
            hover_bg = hex_to_rgba(c["seafoam_deep"], 210)
            press_bg = hex_to_rgba(c["seafoam_deep"], 240)
        elif v == "danger":
            bg = hex_to_rgba(c["coral_dim"], 140)
            border = hex_to_rgba(c["coral"], 100)
            text = c["coral"]
            hover_bg = hex_to_rgba(c["coral_dim"], 200)
            press_bg = hex_to_rgba(c["coral_dim"], 230)
        else:
            bg = glass_bg(140)
            border = glass_edge(70)
            text = c["hd_white"]
            hover_bg = glass_bg(190)
            press_bg = glass_bg_dark(200)

        self.setStyleSheet(f"""
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
                color: {c['text_muted']};
                border: 1px solid {c['border_dim']};
            }}
        """)

    @property
    def variant(self):
        return self._variant

    @variant.setter
    def variant(self, value: str):
        self._variant = value
        self._apply_style()


# ═══════════════════════════════════════════════════════════════
#  GlassPanel
# ═══════════════════════════════════════════════════════════════

class GlassPanel(QFrame):
    """Semi-transparent glass surface panel.

    Drop-in for QFrame with glass styling applied automatically.
    Configure with `radius` and `alpha` kwargs.
    """

    def __init__(self, radius: int = 18, alpha: int = 180, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._alpha = alpha
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {glass_bg(self._alpha)};
                border: 1px solid {glass_edge()};
                border-top: 1px solid {glass_sheen()};
                border-radius: {self._radius}px;
            }}
        """)

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value: int):
        self._radius = value
        self._apply_style()


# ═══════════════════════════════════════════════════════════════
#  GlassSidebar
# ═══════════════════════════════════════════════════════════════

class GlassSidebar(QFrame):
    """Left-side navigation panel with glass background.

    Slightly heavier than GlassPanel for visual hierarchy.
    """

    def __init__(self, radius: int = 18, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {glass_bg_heavy(210)};
                border: 1px solid {glass_edge()};
                border-top: 1px solid {glass_sheen()};
                border-right: 1px solid {glass_edge(30)};
                border-radius: {self._radius}px;
            }}
        """)


# ═══════════════════════════════════════════════════════════════
#  GlassCard
# ═══════════════════════════════════════════════════════════════

class GlassCard(QFrame):
    """Content card with glass surface.

    For metric cards, media tiles, settings groups, etc.
    Optionally takes a `title` string to render a header label.
    """

    def __init__(self, title: str = "", radius: int = 18, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._apply_style()

        if title:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 12, 16, 12)
            header = QLabel(title)
            header.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['seafoam']};
                    font-family: "{FONTS['ui']}";
                    font-weight: bold;
                    font-size: {FONTS['size_lg']}px;
                    background: transparent;
                    border: none;
                }}
            """)
            layout.addWidget(header)

    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {glass_bg(170)};
                border: 1px solid {glass_edge()};
                border-top: 1px solid {glass_sheen()};
                border-radius: {self._radius}px;
            }}
        """)

    def add_content(self, widget: QWidget):
        """Add a widget below the optional title."""
        layout = self.layout()
        if layout is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 12, 16, 12)
        layout.addWidget(widget)


# ═══════════════════════════════════════════════════════════════
#  GlassInput
# ═══════════════════════════════════════════════════════════════

class GlassInput(QLineEdit):
    """Styled line input with glass surface and seafoam focus ring."""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {glass_bg_dark(120)};
                color: {COLORS['hd_white']};
                border: 1px solid {glass_edge(60)};
                border-radius: {RADIUS_SM};
                padding: 6px 12px;
                selection-background-color: {COLORS['seafoam_glow']};
                selection-color: {COLORS['hd_white']};
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
                min-height: 26px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['seafoam']};
                background: {glass_bg_dark(150)};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_muted']};
            }}
            QLineEdit:disabled {{
                color: {COLORS['text_muted']};
                background: {glass_bg_dark(60)};
            }}
        """)


# ═══════════════════════════════════════════════════════════════
#  GlassStatusBar
# ═══════════════════════════════════════════════════════════════

class GlassStatusBar(QStatusBar):
    """Glass-styled status bar with translucent background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QStatusBar {{
                background: {glass_bg(170)};
                color: {COLORS['text_secondary']};
                border-top: 1px solid {glass_edge()};
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_xs']}px;
                padding: 3px 10px;
            }}
            QStatusBar::item {{
                border: none;
                padding: 0 8px;
            }}
        """)


# ═══════════════════════════════════════════════════════════════
#  GlassSectionLabel
# ═══════════════════════════════════════════════════════════════

class GlassSectionLabel(QLabel):
    """Styled section/heading label with seafoam accent."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['seafoam']};
                font-family: "{FONTS['ui']}";
                font-weight: bold;
                font-size: {FONTS['size_lg']}px;
                padding: 4px 0;
                background: transparent;
                border: none;
            }}
        """)


# ═══════════════════════════════════════════════════════════════
#  GlassSeparator
# ═══════════════════════════════════════════════════════════════

class GlassSeparator(QFrame):
    """Horizontal separator line with glass edge styling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet(f"""
            QFrame {{
                background: {glass_edge(40)};
                border: none;
                max-height: 1px;
            }}
        """)
