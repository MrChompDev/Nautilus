"""
Nautilus OS -- Base Window Class

Provides a consistent glassmorphism starting point for all apps.
Subclass NautilusWindow instead of QMainWindow to get automatic
palette setup, glass background, and status bar.

Usage:
    from core.base_window import NautilusWindow

    class MyWindow(NautilusWindow):
        def __init__(self):
            super().__init__(title="My App", size=(1024, 768))
            # build your UI on self.central_widget
"""

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from core.glass_widgets import GlassStatusBar
from core.theme import (
    COLORS,
    RADIUS_LG,
    create_nautilus_palette,
    get_global_stylesheet,
    glass_bg,
)


class NautilusWindow(QMainWindow):
    """Glassmorphism-aware base window for all Nautilus OS apps.

    Sets up:
      - Nautilus palette + global stylesheet (idempotent)
      - A central widget with glass background
      - An optional glass status bar

    Subclasses should build their UI inside `self.central_widget`
    using `self.central_layout` as the root layout.
    """

    def __init__(
        self,
        title: str = "Nautilus",
        size: tuple[int, int] = (1024, 768),
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(*size)

        # Ensure palette + global stylesheet are applied.
        # Multiple calls are safe -- QApplication deduplicates.
        app = QApplication.instance()
        if app is not None:
            if app.palette().window().color().name() != COLORS["abyss_navy"]:
                app.setPalette(create_nautilus_palette())
            if not app.styleSheet():
                app.setStyleSheet(get_global_stylesheet())

        # Central widget with glass surface
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(f"""
            QWidget {{
                background: {glass_bg(180)};
                color: {COLORS['hd_white']};
            }}
        """)
        self.setCentralWidget(self.central_widget)

        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(8, 8, 8, 8)
        self.central_layout.setSpacing(6)

    def add_status_bar(self) -> GlassStatusBar:
        """Add a glass status bar and return it for further configuration."""
        bar = GlassStatusBar(self)
        self.setStatusBar(bar)
        return bar

    def set_glass_background(self, alpha: int = 180, radius: int = RADIUS_LG):
        """Re-apply glass background with custom alpha/radius."""
        self.central_widget.setStyleSheet(f"""
            QWidget {{
                background: {glass_bg(alpha)};
                color: {COLORS['hd_white']};
            }}
        """)


# Lazy import to avoid circular dependency at module level
from PySide6.QtWidgets import QApplication  # noqa: E402
