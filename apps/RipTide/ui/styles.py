"""Riptide Audio - PySide6 Theme & Colors"""
from __future__ import annotations

from core.theme import (
    COLORS,
    RADIUS_LG,
    RADIUS_MD,
    RADIUS_SM,
    glass_bg,
    glass_bg_dark,
    glass_bg_heavy,
    glass_edge,
    glass_sheen,
    hex_to_rgba,
)


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

    glass_bg = glass_bg(170)
    glass_bg_dark = glass_bg_dark(140)
    glass_edge = glass_edge()
    glass_sheen = glass_sheen()


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
    """Global QSS for the Riptide glassmorphism theme."""
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
            background: {glass_bg(140)}; color: {C.TEXT_PRIMARY};
            border: 1px solid {glass_edge(70)}; border-radius: {RADIUS_SM};
            padding: 6px 14px; font-size: 11px;
        }}
        QPushButton:hover {{
            background: {glass_bg(190)}; border-color: {glass_edge(100)}; color: {C.ACCENT};
        }}
        QPushButton:pressed {{
            background: {glass_bg_dark(200)}; border-color: {glass_edge(120)};
        }}
        QPushButton:disabled {{
            color: {C.TEXT_MUTED}; background: {glass_bg_dark(80)}; border-color: {C.BORDER};
        }}

        QPushButton#accent_btn {{
            background: {hex_to_rgba(COLORS["seafoam_deep"], 160)};
            color: {C.ACCENT}; font-weight: bold;
            border: 1px solid {hex_to_rgba(COLORS["seafoam"], 120)};
            border-radius: {RADIUS_SM};
        }}
        QPushButton#accent_btn:hover {{
            background: {hex_to_rgba(COLORS["seafoam_deep"], 210)};
            border-color: {glass_edge(80)};
        }}
        QPushButton#danger_btn {{
            background: {hex_to_rgba(COLORS["coral_dim"], 140)};
            color: {C.DANGER};
            border: 1px solid {hex_to_rgba(COLORS["coral"], 100)};
            border-radius: {RADIUS_SM};
        }}
        QPushButton#danger_btn:hover {{
            background: {hex_to_rgba(COLORS["coral_dim"], 200)};
            color: #ffffff;
        }}
        QPushButton#ghost_btn {{ background: transparent; border: none; color: {C.TEXT_SECONDARY}; }}
        QPushButton#ghost_btn:hover {{ color: {C.ACCENT}; }}

        QLineEdit {{
            background: {glass_bg_dark(120)}; color: {C.TEXT_PRIMARY};
            border: 1px solid {glass_edge(60)}; border-radius: {RADIUS_SM};
            padding: 6px 10px;
        }}
        QLineEdit:focus {{
            border: 1px solid {C.ACCENT}; background: {glass_bg_dark(150)};
        }}

        QComboBox {{
            background: {glass_bg_dark(130)}; color: {C.TEXT_PRIMARY};
            border: 1px solid {glass_edge(60)}; border-radius: {RADIUS_SM}; padding: 5px 10px;
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox QAbstractItemView {{
            background: {glass_bg_heavy(230)}; color: {C.TEXT_PRIMARY};
            border: 1px solid {glass_edge()}; border-radius: {RADIUS_MD};
            selection-background-color: {hex_to_rgba(COLORS["seafoam_deep"], 180)};
            selection-color: {C.ACCENT};
        }}

        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: transparent; width: 10px; margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {hex_to_rgba(COLORS["scrollbar_handle"], 180)};
            min-height: 24px; border-radius: 5px; border: 2px solid transparent;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {hex_to_rgba(COLORS["scrollbar_hover"], 220)};
            border: 2px solid transparent;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        QScrollBar:horizontal {{
            background: transparent; height: 10px; margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {hex_to_rgba(COLORS["scrollbar_handle"], 180)};
            min-width: 24px; border-radius: 5px; border: 2px solid transparent;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {hex_to_rgba(COLORS["scrollbar_hover"], 220)};
            border: 2px solid transparent;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

        QSlider::groove:horizontal {{
            height: 6px; background: {glass_bg_dark(120)}; border: 1px solid {glass_edge(40)};
            border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{
            background: {hex_to_rgba(COLORS["seafoam_deep"], 200)}; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            width: 16px; margin: -6px 0; background: {C.ACCENT};
            border: 2px solid {COLORS["seafoam_dim"]}; border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {COLORS["seafoam_dim"]}; border-color: {C.ACCENT};
        }}

        QListWidget {{
            background: {glass_bg(100)}; color: {C.TEXT_SECONDARY};
            border: none; outline: none; font-size: 12px; border-radius: {RADIUS_MD};
        }}
        QListWidget::item {{ padding: 8px 14px; border: none; border-radius: {RADIUS_SM}; }}
        QListWidget::item:hover {{ background: {glass_bg(140)}; color: {C.TEXT_PRIMARY}; }}
        QListWidget::item:selected {{
            background: {hex_to_rgba(COLORS["surface_selected"], 180)}; color: {C.ACCENT};
            border-left: 3px solid {C.ACCENT};
        }}
        QListWidget::item:disabled {{
            color: {C.TEXT_MUTED}; font-weight: bold; font-size: 10px; padding: 10px 14px 2px 14px;
        }}

        QFrame#card {{
            background: {glass_bg(185)}; border: 1px solid {glass_edge()};
            border-top: 1px solid {glass_sheen()};
            border-radius: {RADIUS_LG};
        }}
        QFrame#card:hover {{ border-color: {glass_edge(80)}; }}
        QFrame#trackrow {{
            background: {glass_bg(100)}; border: none; border-radius: {RADIUS_SM};
        }}
        QFrame#trackrow:hover {{ background: {glass_bg(160)}; }}
        QFrame#nowplaying {{
            background: {glass_bg_heavy(210)}; border-top: 1px solid {glass_edge()};
        }}
        QFrame#sfxbtn {{
            background: {glass_bg(140)}; border: 2px solid {glass_edge()};
            border-radius: {RADIUS_MD}; color: {C.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;
        }}
        QFrame#sfxbtn:hover {{ background: {glass_bg(190)}; }}
        QDialog {{ background-color: {C.BG_PRIMARY}; }}
        QMessageBox {{ background-color: {C.BG_PRIMARY}; }}
        QInputDialog {{ background-color: {C.BG_PRIMARY}; }}
        QMenu {{
            background: {glass_bg_heavy(230)}; color: {C.TEXT_PRIMARY};
            border: 1px solid {glass_edge()}; border-radius: {RADIUS_MD};
        }}
        QMenu::item:selected {{
            background: {hex_to_rgba(COLORS["seafoam_deep"], 180)}; color: {C.ACCENT};
        }}

        QProgressBar {{
            background: {glass_bg_dark(100)}; border: 1px solid {glass_edge(50)};
            border-radius: 4px; text-align: center; color: {C.TEXT_PRIMARY};
            height: 8px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS["seafoam_deep"]}, stop:1 {C.ACCENT});
            border-radius: 3px;
        }}
    """


def apply_dark_theme(app) -> None:
    from PySide6.QtGui import QColor, QPalette

    C = Colors
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(C.BG_PRIMARY))
    pal.setColor(QPalette.WindowText, QColor(C.TEXT_PRIMARY))
    pal.setColor(QPalette.Base, QColor(COLORS["deep_navy"]))
    pal.setColor(QPalette.AlternateBase, QColor(COLORS["slate_navy"]))
    pal.setColor(QPalette.Text, QColor(C.TEXT_PRIMARY))
    pal.setColor(QPalette.Button, QColor(COLORS["slate_navy"]))
    pal.setColor(QPalette.ButtonText, QColor(C.TEXT_PRIMARY))
    pal.setColor(QPalette.Highlight, QColor(C.ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor(COLORS["void_black"]))
    pal.setColor(QPalette.ToolTipBase, QColor(COLORS["slate_navy"]))
    pal.setColor(QPalette.ToolTipText, QColor(C.TEXT_PRIMARY))
    pal.setColor(QPalette.PlaceholderText, QColor(C.TEXT_MUTED))
    app.setPalette(pal)
    app.setStyleSheet(build_stylesheet())
