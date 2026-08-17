"""Cinema — reusable UI widgets: media cards, grid, sidebar, art loader."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from apps.Cinema.src.library import MediaItem

try:
    from core.theme import COLORS, FONTS, SPACING, glass_bg, glass_bg_dark, glass_edge, glass_sheen
except ImportError:
    COLORS = {"abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
              "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
              "seafoam_deep": "#004D40", "coral": "#FF7F50", "amber": "#FFA502",
              "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8", "text_muted": "#506070",
              "border": "#152D44", "surface_hover": "#132A40", "surface_selected": "#1A3352"}
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11,
             "size_md": 12, "size_lg": 13, "size_xl": 14}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16}

    def hex_to_rgba(h, a=255):
        v = h.lstrip("#")
        return f"rgba({int(v[0:2],16)},{int(v[2:4],16)},{int(v[4:6],16)},{a})"
    def glass_bg(a=180): return hex_to_rgba(COLORS["slate_navy"], a)
    def glass_bg_dark(a=140): return hex_to_rgba(COLORS["deep_navy"], a)
    def glass_edge(a=48): return hex_to_rgba(COLORS["seafoam"], a)
    def glass_sheen(): return "rgba(238, 244, 248, 26)"


class ArtCache:
    """Simple in-memory pixmap cache shared app-wide."""

    def __init__(self):
        self._pixmaps: dict[str, QPixmap] = {}
        self._pending: dict[str, list] = {}

    def get(self, key: str):
        return self._pixmaps.get(key)

    def put(self, key: str, pixmap: QPixmap):
        self._pixmaps[key] = pixmap
        for cb in self._pending.pop(key, []):
            try:
                cb(pixmap)
            except Exception:
                pass

    def on_ready(self, key: str, cb):
        if key in self._pixmaps:
            cb(self._pixmaps[key])
            return
        self._pending.setdefault(key, []).append(cb)


ART_CACHE = ArtCache()


class ArtLoader(QThread):
    """Background thread to load poster art (file or URL) without stalling UI."""

    loaded = Signal(str, QPixmap)

    def __init__(self, jobs: list[tuple], parent=None):
        super().__init__(parent)
        self._jobs = jobs

    def run(self):
        from PySide6.QtGui import QPixmap
        for key, src, size in self._jobs:
            if ART_CACHE.get(key):
                continue
            pix = QPixmap()
            if isinstance(src, str):
                if src.startswith(("http://", "https://")):
                    pix = QPixmap()  # remote handled by caller via QNetworkAccessManager
                    continue
                if os.path.isfile(src):
                    pix = QPixmap(src)
            if not pix.isNull():
                if size:
                    pix = pix.scaled(size, size, Qt.KeepAspectRatioByExpanding,
                                     Qt.SmoothTransformation)
                ART_CACHE.put(key, pix)
                self.loaded.emit(key, pix)


class MediaCard(QFrame):
    """A clickable poster card for a movie/show."""

    clicked = Signal(object)
    play_requested = Signal(object)
    fav_toggled = Signal(object, bool)
    remove_requested = Signal(object)

    def __init__(self, item: MediaItem, favorite: bool = False, parent=None):
        super().__init__(parent)
        self.item = item
        self.favorite = favorite
        self.setFixedSize(168, 268)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            MediaCard {{
                background-color: {glass_bg(170)};
                border: 1px solid {glass_edge()};
                border-radius: 18px;
                border-top: 1px solid {glass_sheen()};
            }}
            MediaCard:hover {{ border-color: {COLORS['seafoam']}; background-color: {glass_bg(200)}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["sm"], SPACING["sm"], SPACING["sm"], SPACING["sm"])
        layout.setSpacing(SPACING["xs"])

        self._poster = QLabel()
        self._poster.setFixedSize(152, 216)
        self._poster.setAlignment(Qt.AlignCenter)
        self._poster.setText("\U0001F3AC")
        self._poster.setStyleSheet(f"""
            background-color: {glass_bg_dark(120)};
            border: 1px solid {glass_edge()};
            border-radius: 12px;
            border-top: 1px solid {glass_sheen()};
            color: {COLORS['text_muted']}; font-size: 28px;
        """)
        layout.addWidget(self._poster)

        self._title = QLabel(item.title)
        self._title.setWordWrap(True)
        self._title.setAlignment(Qt.AlignLeft)
        self._title.setFixedHeight(34)
        self._title.setStyleSheet(f"""
            color: {COLORS['hd_white']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px; background: transparent; border: none;
        """)
        layout.addWidget(self._title)

        self._fav_btn = QPushButton("\u2606")
        self._fav_btn.setFixedSize(24, 20)
        self._fav_btn.setToolTip("Favorite")
        self._fav_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['amber']}; border: none;
                font-size: 13px;
            }}
            QPushButton:hover {{ color: {COLORS['seafoam']}; }}
        """)
        self._update_fav_icon()
        self._fav_btn.clicked.connect(self._on_fav)
        layout.addWidget(self._fav_btn, 0, Qt.AlignRight)

    def _update_fav_icon(self):
        self._fav_btn.setText("\u2605" if self.favorite else "\u2606")

    def _on_fav(self):
        self.favorite = not self.favorite
        self._update_fav_icon()
        self.fav_toggled.emit(self.item, self.favorite)

    def set_poster(self, pixmap: QPixmap):
        self._poster.setPixmap(
            pixmap.scaled(152, 216, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        )

    def set_placeholder_text(self, text: str):
        self._poster.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.item)

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {glass_bg(200)}; color: {COLORS['hd_white']};
                      border: 1px solid {glass_edge()}; border-radius: 10px;
                      border-top: 1px solid {glass_sheen()}; }}
            QMenu::item:selected {{ background-color: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']}; }}
        """)
        play = menu.addAction("\u25B6  Play")
        fav = menu.addAction("\u2605  Favorite" if not self.favorite else "\u2606  Unfavorite")
        if self.item.kind in ("movie", "episode"):
            menu.addSeparator()
            remove = menu.addAction("\u2716  Remove from Library")
        else:
            remove = None
        act = menu.exec(event.globalPos())
        if act == play:
            self.play_requested.emit(self.item)
        elif act == fav:
            self._on_fav()
        elif act is not None and act == remove:
            self.remove_requested.emit(self.item)


class MediaGrid(QScrollArea):
    """Scrollable grid of media cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._layout = QGridLayout(self._container)
        self._layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        self._layout.setSpacing(SPACING["lg"])
        self._layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setWidget(self._container)
        self._cards: list[MediaCard] = []
        self._cols = 5

    def clear(self):
        for card in self._cards:
            card.deleteLater()
        self._cards = []
        self._clear_layout()

    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def add_item(self, item: MediaItem, favorite: bool = False) -> MediaCard:
        card = MediaCard(item, favorite)
        idx = len(self._cards)
        self._layout.addWidget(card, idx // self._cols, idx % self._cols)
        self._cards.append(card)
        return card

    def set_columns(self, cols: int):
        self._cols = max(1, cols)
        # Re-layout existing cards
        for i, card in enumerate(self._cards):
            self._layout.addWidget(card, i // self._cols, i % self._cols)

    def cards(self) -> list[MediaCard]:
        return list(self._cards)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = event.size().width()
        cols = max(1, int(w / 180))
        if cols != self._cols and self._cards:
            self._cols = cols
            for i, card in enumerate(self._cards):
                self._layout.addWidget(card, i // self._cols, i % self._cols)


class Sidebar(QListWidget):
    """Left navigation rail: sections + server status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(190)
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {glass_bg(160)};
                color: {COLORS['text_secondary']};
                border: none;
                border-right: 1px solid {glass_edge()};
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
                outline: none;
            }}
            QListWidget::item {{ padding: 8px 12px; border: none; border-radius: 6px; margin: 2px 4px; }}
            QListWidget::item:hover {{ background-color: {glass_bg(80)}; color: {COLORS['hd_white']}; }}
            QListWidget::item:selected {{ background-color: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']}; border-radius: 6px; }}
        """)

    def add_section(self, text: str):
        item = QListWidgetItem(text.upper())
        item.setFlags(Qt.NoItemFlags)
        item.setForeground(Qt.gray)
        font = item.font()
        font.setBold(True)
        font.setPointSize(9)
        item.setFont(font)
        self.addItem(item)

    def add_entry(self, label: str, data: str) -> QListWidgetItem:
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, data)
        self.addItem(item)
        return item

    def set_status(self, text: str, connected: bool = False):
        self.setToolTip(f"Library: {text}")
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == "__status__":
                item.setText(text)
                item.setForeground(Qt.green if connected else Qt.gray)
                return
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, "__status__")
        item.setForeground(Qt.green if connected else Qt.gray)
        self.addItem(item)


class EmptyState(QWidget):
    """Friendly empty-state placeholder with an action button."""

    def __init__(self, icon: str, title: str, subtitle: str, btn_text: str = "",
                 parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(SPACING["md"])

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"color: {COLORS['seafoam']}; font-size: 48px; background: transparent;")
        layout.addWidget(icon_lbl)

        t = QLabel(title)
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(f"color: {COLORS['hd_white']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_lg']}px; background: transparent;")
        layout.addWidget(t)

        s = QLabel(subtitle)
        s.setAlignment(Qt.AlignCenter)
        s.setWordWrap(True)
        s.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px; background: transparent;")
        s.setMaximumWidth(420)
        layout.addWidget(s)

        self._btn = None
        if btn_text:
            self._btn = QPushButton(btn_text)
            self._btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']};
                    border: 1px solid {COLORS['seafoam']}; padding: 8px 18px;
                    font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
                }}
                QPushButton:hover {{ background-color: {COLORS['seafoam']}; color: {COLORS['void_black']}; }}
            """)
            layout.addWidget(self._btn, 0, Qt.AlignCenter)

    def on_clicked(self, cb):
        if self._btn:
            self._btn.clicked.connect(cb)


class BusyBar(QWidget):
    """Indeterminate progress bar used during scans/fetches."""

    def __init__(self, text: str = "Working...", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])

        self._lbl = QLabel(text)
        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_sm']}px; background: transparent;")
        layout.addWidget(self._lbl)

        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setFixedHeight(4)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{ background: {glass_bg_dark(100)}; border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {COLORS['seafoam']}; border-radius: 2px; }}
        """)
        layout.addWidget(bar)

    def set_text(self, text: str):
        self._lbl.setText(text)


def section_header(title: str, subtitle: str = "") -> QLabel:
    lbl = QLabel(title)
    lbl.setStyleSheet(f"""
        color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
        font-size: {FONTS['size_xl']}px; font-weight: bold; letter-spacing: 2px;
        padding: 6px 0; border-bottom: 1px solid {glass_edge()};
        background: transparent;
    """)
    return lbl
