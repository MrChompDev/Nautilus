"""Riptide Audio - PySide6 Theme & Colors"""
from __future__ import annotations

from core.theme import COLORS


class Colors:
    BG_PRIMARY = COLORS["abyss_navy"]
    BG_SECONDARY = COLORS["slate_navy"]
    BG_TERTIARY = COLORS["deep_navy"]
    BG_CARD = COLORS["void_black"]
    BG_HOVER = COLORS["surface_hover"]
    BG_ACTIVE = COLORS["surface_pressed"]
    ACCENT = COLORS["seafoam"]
    ACCENT_HOVER = COLORS["seafoam_dim"]
    ACCENT_DIM = COLORS["seafoam_glow"]
    TEXT_PRIMARY = COLORS["hd_white"]
    TEXT_SECONDARY = COLORS["text_secondary"]
    TEXT_MUTED = COLORS["text_muted"]
    BORDER = COLORS["border"]
    BORDER_LIGHT = COLORS["border_dim"]
    DANGER = COLORS["coral"]
    SUCCESS = COLORS["emerald"]
    WARNING = COLORS["amber"]
    SPOTIFY = COLORS["text_secondary"]  # placeholder - use Spotify logo color
    YOUTUBE = COLORS["text_secondary"]  # placeholder - use YouTube logo color
    SOUNDCLOUD = COLORS["text_secondary"]  # placeholder - use SoundCloud logo color


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _ui_font() -> str:
    try:
        from core.theme import FONTS
        return FONTS.get("ui", "Segoe UI")
    except Exception:
        return "Segoe UI"


def build_stylesheet() -> str:
    """Global QSS for the Riptide dark theme."""
    C = Colors
    font = _ui_font()
    return f"""
        QMainWindow, QWidget {{
            background-color: {C.BG_PRIMARY}; color: {C.TEXT_PRIMARY};
            font-family: "{font}"; font-size: 11px;
        }}
        QLabel {{ background: transparent; }}
        QLabel#page_title {{
            color: {C.TEXT_PRIMARY}; font-size: 18px; font-weight: bold;
            background: transparent; padding: 4px;
        }}
        QLabel#section_title {{
            color: {C.TEXT_SECONDARY}; font-size: 13px; font-weight: bold;
            background: transparent; padding-top: 12px;
        }}
        QLabel#muted {{ color: {C.TEXT_MUTED}; background: transparent; }}

        QPushButton {{
            background-color: {C.BG_TERTIARY}; color: {C.TEXT_PRIMARY};
            border: 1px solid {C.BORDER_LIGHT}; border-radius: 4px;
            padding: 6px 14px; font-size: 11px;
        }}
        QPushButton:hover {{ background-color: {C.BG_HOVER}; border-color: {C.ACCENT}; }}
        QPushButton:disabled {{ color: {C.TEXT_MUTED}; border-color: {C.BORDER}; }}

        QPushButton#accent_btn {{
            background-color: {C.ACCENT}; color: {C.BG_PRIMARY};
            border: 1px solid {C.ACCENT}; font-weight: bold;
        }}
        QPushButton#accent_btn:hover {{ background-color: {C.ACCENT_HOVER}; }}
        QPushButton#danger_btn {{
            background-color: transparent; color: {C.DANGER};
            border: 1px solid {C.DANGER};
        }}
        QPushButton#danger_btn:hover {{ background-color: {C.DANGER}; color: #ffffff; }}
        QPushButton#ghost_btn {{ background-color: transparent; border: none; color: {C.TEXT_SECONDARY}; }}
        QPushButton#ghost_btn:hover {{ color: {C.ACCENT}; }}

        QLineEdit {{
            background-color: {C.BG_TERTIARY}; color: {C.TEXT_PRIMARY};
            border: 1px solid {C.BORDER_LIGHT}; border-radius: 4px; padding: 6px 10px;
        }}
        QLineEdit:focus {{ border-color: {C.ACCENT}; }}

        QComboBox {{
            background-color: {C.BG_TERTIARY}; color: {C.TEXT_PRIMARY};
            border: 1px solid {C.BORDER_LIGHT}; border-radius: 4px; padding: 5px 10px;
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox QAbstractItemView {{
            background-color: {C.BG_SECONDARY}; color: {C.TEXT_PRIMARY};
            border: 1px solid {C.BORDER_LIGHT}; selection-background-color: {C.ACCENT_DIM};
        }}

        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: {C.BG_PRIMARY}; width: 10px; margin: 0;
        }}
        QScrollBar::handle:vertical {{ background: {C.BORDER_LIGHT}; border-radius: 4px; min-height: 24px; }}
        QScrollBar::handle:vertical:hover {{ background: {C.ACCENT_DIM}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ background: {C.BG_PRIMARY}; height: 10px; margin: 0; }}
        QScrollBar::handle:horizontal {{ background: {C.BORDER_LIGHT}; border-radius: 4px; min-width: 24px; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

        QSlider::groove:horizontal {{
            height: 4px; background: {C.BG_TERTIARY}; border-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{ background: {C.ACCENT}; border-radius: 2px; }}
        QSlider::handle:horizontal {{
            width: 12px; margin: -4px 0; background: {C.ACCENT};
            border-radius: 6px;
        }}
        QSlider::handle:horizontal:hover {{ background: {C.ACCENT_HOVER}; }}

        QListWidget {{
            background-color: {C.BG_SECONDARY}; color: {C.TEXT_SECONDARY};
            border: none; outline: none; font-size: 12px;
        }}
        QListWidget::item {{ padding: 8px 14px; border: none; }}
        QListWidget::item:hover {{ background-color: {C.BG_HOVER}; color: {C.TEXT_PRIMARY}; }}
        QListWidget::item:selected {{
            background-color: {C.ACCENT_DIM}; color: {C.ACCENT};
            border-left: 3px solid {C.ACCENT};
        }}
        QListWidget::item:disabled {{
            color: {C.TEXT_MUTED}; font-weight: bold; font-size: 10px; padding: 10px 14px 2px 14px;
        }}

        QFrame#card {{
            background-color: {C.BG_CARD}; border: 1px solid {C.BORDER};
            border-radius: 6px;
        }}
        QFrame#card:hover {{ border-color: {C.BORDER_LIGHT}; }}
        QFrame#trackrow {{ background-color: {C.BG_CARD}; border: none; border-radius: 4px; }}
        QFrame#trackrow:hover {{ background-color: {C.BG_HOVER}; }}
        QFrame#nowplaying {{
            background-color: {C.BG_SECONDARY}; border-top: 1px solid {C.BORDER};
        }}
        QFrame#sfxbtn {{
            background-color: {C.BG_TERTIARY}; border: 2px solid {C.BORDER_LIGHT};
            border-radius: 8px; color: {C.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;
        }}
        QFrame#sfxbtn:hover {{ background-color: {C.BG_HOVER}; }}
        QDialog {{ background-color: {C.BG_PRIMARY}; }}
        QMessageBox {{ background-color: {C.BG_PRIMARY}; }}
        QInputDialog {{ background-color: {C.BG_PRIMARY}; }}
        QMenu {{ background-color: {C.BG_SECONDARY}; color: {C.TEXT_PRIMARY};
                 border: 1px solid {C.BORDER_LIGHT}; }}
        QMenu::item:selected {{ background-color: {C.ACCENT_DIM}; color: {C.ACCENT}; }}
    """


def apply_dark_theme(app) -> None:
    from PySide6.QtGui import QColor, QPalette

    C = Colors
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(C.BG_PRIMARY))
    pal.setColor(QPalette.WindowText, QColor(C.TEXT_PRIMARY))
    pal.setColor(QPalette.Base, QColor(C.BG_TERTIARY))
    pal.setColor(QPalette.AlternateBase, QColor(C.BG_CARD))
    pal.setColor(QPalette.Text, QColor(C.TEXT_PRIMARY))
    pal.setColor(QPalette.Button, QColor(C.BG_TERTIARY))
    pal.setColor(QPalette.ButtonText, QColor(C.TEXT_PRIMARY))
    pal.setColor(QPalette.Highlight, QColor(C.ACCENT_DIM))
    pal.setColor(QPalette.HighlightedText, QColor(C.ACCENT))
    pal.setColor(QPalette.ToolTipBase, QColor(C.BG_SECONDARY))
    pal.setColor(QPalette.ToolTipText, QColor(C.TEXT_PRIMARY))
    pal.setColor(QPalette.PlaceholderText, QColor(C.TEXT_MUTED))
    app.setPalette(pal)
    app.setStyleSheet(build_stylesheet())
