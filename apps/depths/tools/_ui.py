"""Shared UI helpers for Depth tools."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.theme import COLORS, FONTS

TOOL_BG = COLORS["bg_light"]
INPUT_STYLE = f"""
QLineEdit {{
    background: {COLORS['bg_mid']};
    color: {COLORS['text_dark']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 10px;
    font-family: "{FONTS['mono']}";
    font-size: {FONTS['size_md']}px;
}}
QLineEdit:focus {{
    border: 1px solid {COLORS['coral']};
}}
"""

BTN_STYLE = f"""
QPushButton {{
    background: {COLORS['teal']}; color: #fff;
    border: none; border-radius: 8px;
    padding: 8px 16px; font-size: {FONTS['size_sm']}px;
    font-weight: bold;
}}
QPushButton:hover {{ background: {COLORS['teal_light']}; }}
QPushButton:disabled {{ background: {COLORS['border']}; }}
"""

OUT_STYLE = f"""
QTextEdit {{
    background: {COLORS['bg_dark']};
    color: {COLORS['scan_green']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    font-family: "{FONTS['mono']}";
    font-size: {FONTS['size_sm']}px;
    padding: 10px;
}}
"""

GREEN = COLORS["scan_green"]
RED = COLORS["alert_red"]
YELLOW = COLORS["warning"]
CYAN = COLORS["teal_light"]


def make_header(title, subtitle=""):
    header = QWidget()
    layout = QVBoxLayout(header)
    layout.setContentsMargins(0, 0, 0, 4)
    layout.setSpacing(2)
    t = QLabel(title)
    t.setStyleSheet(f"color: {COLORS['teal_light']}; font-family: \"{FONTS['ui']}\"; font-size: {FONTS['size_xl']}px; font-weight: bold; background: transparent; border: none;")
    layout.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px; background: transparent; border: none;")
        layout.addWidget(s)
    return header


def hline():
    from PySide6.QtWidgets import QFrame
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {COLORS['border']}; border: none;")
    return f
