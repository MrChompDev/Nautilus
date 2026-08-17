"""Cinema — Nautilus Media Center main window.

A fully local, offline media center. You add your own movies and shows to
"My Media" and Cinema scans, indexes, and plays them back with a poster grid
UI. No servers, no accounts — everything stays on this device.
"""

from __future__ import annotations

import os
import re
import shutil

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from apps.Cinema.src.library import MEDIA_EXTENSIONS, LibraryScanner, MediaItem, _clean_title
from apps.Cinema.src.player import PlayerWindow
from apps.Cinema.src.settings import CinemaSettings
from apps.Cinema.src.widgets import (
    ART_CACHE,
    BusyBar,
    EmptyState,
    MediaCard,
    MediaGrid,
    Sidebar,
    section_header,
)

try:
    from core.theme import COLORS, FONTS, SPACING, glass_bg, glass_bg_dark, glass_edge, glass_sheen
except ImportError:
    COLORS = {"abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
              "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
              "seafoam_deep": "#004D40", "coral": "#FF7F50", "amber": "#FFA502",
              "emerald": "#00C853", "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8",
              "text_muted": "#506070", "border": "#152D44", "surface_hover": "#132A40",
              "surface_selected": "#1A3352"}
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11,
             "size_md": 12, "size_lg": 13, "size_xl": 14, "size_xxl": 16, "size_title": 20}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "xxl": 24, "xxxl": 32}

    def hex_to_rgba(h, a=255):
        v = h.lstrip("#")
        return f"rgba({int(v[0:2],16)},{int(v[2:4],16)},{int(v[4:6],16)},{a})"
    def glass_bg(a=180): return hex_to_rgba(COLORS["slate_navy"], a)
    def glass_bg_dark(a=140): return hex_to_rgba(COLORS["deep_navy"], a)
    def glass_edge(a=48): return hex_to_rgba(COLORS["seafoam"], a)
    def glass_sheen(): return "rgba(238, 244, 248, 26)"

DISCLAIMER = (
    "Cinema is a tool for playing media that you own or are licensed to use. "
    "Downloading, streaming, or sharing pirated content is illegal. Keep your "
    "library legal — it's on you, not on us."
)
_EPISODE_RE = re.compile(r"[sS]\d{1,2}[eE]\d{1,2}")
_VIDEO_FILTER = "Video files (" + " ".join("*" + e for e in sorted(MEDIA_EXTENSIONS)) + ")"


def _default_library_dir() -> str:
    return os.path.join(os.path.expanduser("~"), "Cinema")


def _default_media_folders() -> list:
    lib = _default_library_dir()
    return [os.path.join(lib, "Movies"), os.path.join(lib, "TV")]


class CinemaWindow(QMainWindow):
    """Main media-center window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cinema — Media Center")
        self.setMinimumSize(980, 620)
        self.resize(1280, 800)

        self._app_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "..", "..", "data", "cinema"))
        self._cache_dir = self._app_dir
        os.makedirs(self._app_dir, exist_ok=True)

        self._settings = CinemaSettings.load(os.path.join(self._app_dir, "settings.json"))
        if not self._settings.media_folders:
            self._settings.media_folders = _default_media_folders()
            self._settings.save(os.path.join(self._app_dir, "settings.json"))
        for folder in self._settings.media_folders:
            os.makedirs(folder, exist_ok=True)

        self._scanner = LibraryScanner(self._cache_dir)
        self._player: PlayerWindow | None = None
        self._library: list[MediaItem] = []

        self._setup_ui()
        self._setup_shortcuts()

        # Start with cached library, then rescan in background
        self._library = self._scanner.load_cache()
        self._show_home()
        QTimer.singleShot(200, self._rescan_if_stale)
        QTimer.singleShot(0, self._maybe_show_disclaimer)

    # ═══════════════════════════════════════════════════════════════
    #  UI BUILD
    # ═══════════════════════════════════════════════════════════════

    def _setup_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background: {glass_bg_dark(200)};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──
        top = QFrame()
        top.setFixedHeight(48)
        top.setStyleSheet(f"background-color: {glass_bg_dark(220)}; border-bottom: 1px solid {glass_edge()};")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(SPACING["md"], 0, SPACING["md"], 0)
        tl.setSpacing(SPACING["md"])

        self._brand = QLabel("\U0001F3AC  CINEMA  //  Media Center")
        self._brand.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_lg']}px; font-weight: bold; letter-spacing: 2px;
            background: transparent;
        """)
        tl.addWidget(self._brand)

        tl.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search your library…")
        self._search.setFixedWidth(320)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {glass_bg(120)}; color: {COLORS['hd_white']};
                border: 1px solid {glass_edge()}; border-radius: 8px;
                border-top: 1px solid {glass_sheen()};
                padding: 6px 12px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['seafoam']}; }}
        """)
        self._search.returnPressed.connect(self._on_search)
        tl.addWidget(self._search)

        tl.addWidget(self._mk_btn("\U0001F50D", "Search", self._on_search))

        root.addWidget(top)

        # ── Body ──
        body = QSplitter(Qt.Horizontal)
        body.setHandleWidth(1)
        body.setStyleSheet(f"QSplitter::handle {{ background: {glass_edge()}; }}")

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.add_section("Library")
        self._sidebar.add_entry("\U0001F3E0  Home", "home")
        self._sidebar.add_entry("\U0001F3AC  Movies", "movies")
        self._sidebar.add_entry("\U0001F4FA  TV Shows", "shows")
        self._sidebar.add_entry("\u2605  Favorites", "favorites")
        self._sidebar.add_section("Media")
        self._sidebar.add_entry("\U0001F4C2  My Media", "media")
        self._sidebar.add_section("System")
        self._sidebar.add_entry("\u2699  Settings", "settings")
        self._sidebar.currentItemChanged.connect(self._on_sidebar)
        body.addWidget(self._sidebar)

        # Content stack
        self._stack = QStackedWidget()
        body.addWidget(self._stack)
        body.setStretchFactor(1, 1)
        body.setSizes([190, 1090])
        root.addWidget(body, 1)

        # Status bar
        status = QFrame()
        status.setFixedHeight(24)
        status.setStyleSheet(f"background-color: {glass_bg(160)}; border-top: 1px solid {glass_edge()};")
        sl = QHBoxLayout(status)
        sl.setContentsMargins(SPACING["md"], 0, SPACING["md"], 0)
        self._status = QLabel("Ready")
        self._status.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px; background: transparent;")
        sl.addWidget(self._status)
        sl.addStretch()
        self._busy = BusyBar("", status)
        self._busy.setVisible(False)
        sl.addWidget(self._busy)
        root.addWidget(status)

        # Pre-build pages
        self._home_page = QWidget()
        self._movies_page = QWidget()
        self._shows_page = QWidget()
        self._favs_page = QWidget()
        self._media_page = QWidget()
        self._search_page = QWidget()
        self._detail_page = QWidget()
        self._settings_page = QWidget()
        for p in (self._home_page, self._movies_page, self._shows_page,
                  self._favs_page, self._media_page, self._search_page,
                  self._detail_page, self._settings_page):
            self._stack.addWidget(p)

        self._build_home_page()
        self._build_collection_pages()
        self._build_media_page()
        self._build_search_page()
        self._build_detail_page()
        self._build_settings_page()

        self._select_sidebar("home")

    def _mk_btn(self, text: str, tip: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tip)
        btn.setFixedSize(34, 30)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['seafoam']};
                border: 1px solid {glass_edge()}; border-radius: 6px;
                border-top: 1px solid {glass_sheen()};
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {glass_bg(80)}; border-color: {COLORS['seafoam']}; }}
        """)
        btn.clicked.connect(slot)
        return btn

    def _mk_action_btn(self, text: str, slot, primary: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        if primary:
            style = f"""
                QPushButton {{
                    background: {COLORS['seafoam']}; color: {COLORS['void_black']};
                    border: 1px solid {COLORS['seafoam']}; padding: 8px 18px;
                    font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px; font-weight: bold;
                }}
                QPushButton:hover {{ background: {COLORS['seafoam_dim']}; }}
            """
        else:
            style = f"""
                QPushButton {{
                    background: {glass_bg(140)}; color: {COLORS['seafoam']};
                    border: 1px solid {COLORS['seafoam']}; border-radius: 8px;
                    border-top: 1px solid {glass_sheen()};
                    padding: 8px 18px;
                    font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
                }}
                QPushButton:hover {{ background: {COLORS['seafoam_deep']}; }}
            """
        btn.setStyleSheet(style)
        btn.clicked.connect(slot)
        return btn

    def _page(self, name: str) -> QWidget:
        return {
            "home": self._home_page, "movies": self._movies_page,
            "shows": self._shows_page, "favorites": self._favs_page,
            "media": self._media_page, "search": self._search_page,
            "detail": self._detail_page, "settings": self._settings_page,
        }[name]

    def _build_home_page(self):
        layout = QVBoxLayout(self._home_page)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])
        layout.addWidget(section_header("HOME"))

        self._home_empty = EmptyState("\U0001F3AC", "Welcome to Cinema",
            "Your library is empty. Add your own movies and shows to get started.",
            "Import Media")
        self._home_empty.on_clicked(self._import_media)
        layout.addWidget(self._home_empty)

        self._home_resume_label = QLabel("CONTINUE WATCHING")
        self._home_resume_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_sm']}px; letter-spacing: 1px; background: transparent;")
        layout.addWidget(self._home_resume_label)
        self._home_resume = MediaGrid()
        layout.addWidget(self._home_resume, 2)

        self._home_latest_label = QLabel("RECENTLY ADDED")
        self._home_latest_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_sm']}px; letter-spacing: 1px; background: transparent;")
        layout.addWidget(self._home_latest_label)
        self._home_latest = MediaGrid()
        layout.addWidget(self._home_latest, 3)

        layout.addWidget(self._make_disclaimer_box())

    def _build_collection_pages(self):
        # Movies
        mv = QVBoxLayout(self._movies_page)
        mv.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        mv.setSpacing(SPACING["sm"])
        mv.addWidget(section_header("MOVIES"))
        self._movies_empty = EmptyState("\U0001F3AC", "No movies yet",
            "Import your own movies from My Media — everything stays on this device.",
            "Import Media")
        self._movies_empty.on_clicked(self._import_media)
        mv.addWidget(self._movies_empty)
        self._movies_grid = MediaGrid()
        mv.addWidget(self._movies_grid, 1)

        # Shows
        sv = QVBoxLayout(self._shows_page)
        sv.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        sv.setSpacing(SPACING["sm"])
        sv.addWidget(section_header("TV SHOWS"))
        self._shows_empty = EmptyState("\U0001F4FA", "No TV shows yet",
            "Import episodes from My Media — Cinema groups them by show.",
            "Import Media")
        self._shows_empty.on_clicked(self._import_media)
        sv.addWidget(self._shows_empty)
        self._shows_grid = MediaGrid()
        sv.addWidget(self._shows_grid, 1)

        # Favorites
        fv = QVBoxLayout(self._favs_page)
        fv.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        fv.setSpacing(SPACING["sm"])
        fv.addWidget(section_header("FAVORITES"))
        self._favs_empty = EmptyState("\u2605", "No favorites yet",
            "Click the star on any title to add it to Favorites.")
        fv.addWidget(self._favs_empty)
        self._favs_grid = MediaGrid()
        fv.addWidget(self._favs_grid, 1)

    def _build_media_page(self):
        layout = QVBoxLayout(self._media_page)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])
        layout.addWidget(section_header("MY MEDIA"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(self._mk_action_btn("\U0001F4E5  Import Media…", self._import_media, primary=True))
        toolbar.addWidget(self._mk_action_btn("\U0001F4C1  Import Folder…", self._import_folder))
        toolbar.addWidget(self._mk_action_btn("\U0001F4C2  Open Library Folder", self._open_library_folder))
        toolbar.addWidget(self._mk_action_btn("\u21BB  Rescan", self._rescan_manual))
        toolbar.addStretch()
        layout.addLayout(toolbar)

        layout.addWidget(self._make_disclaimer_box())

        self._media_empty = EmptyState("\U0001F4C2", "Nothing imported yet",
            "Import your own movies and shows. Files land in your Cinema folder "
            "(~/Cinema) and are scanned into the library automatically.",
            "Import Media")
        self._media_empty.on_clicked(self._import_media)
        layout.addWidget(self._media_empty)
        self._media_grid = MediaGrid()
        layout.addWidget(self._media_grid, 1)

    def _build_search_page(self):
        sp = QVBoxLayout(self._search_page)
        sp.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        sp.setSpacing(SPACING["sm"])
        sp.addWidget(section_header("SEARCH RESULTS"))
        self._search_empty = EmptyState("\U0001F50D", "No results",
            "Try a different title.")
        sp.addWidget(self._search_empty)
        self._search_grid = MediaGrid()
        sp.addWidget(self._search_grid, 1)

    def _build_detail_page(self):
        layout = QVBoxLayout(self._detail_page)
        layout.setContentsMargins(SPACING["xxl"], SPACING["lg"], SPACING["xxl"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        back = QPushButton("\u2190  Back")
        back.setCursor(Qt.PointingHandCursor)
        back.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {COLORS['text_secondary']};
                border: none; font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px; text-align: left; }}
            QPushButton:hover {{ color: {COLORS['seafoam']}; }}
        """)
        back.clicked.connect(self._go_back_from_detail)
        layout.addWidget(back)

        self._detail_title = QLabel("")
        self._detail_title.setWordWrap(True)
        self._detail_title.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xxl']}px; font-weight: bold; background: transparent;
        """)
        layout.addWidget(self._detail_title)

        self._detail_meta = QLabel("")
        self._detail_meta.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_sm']}px; background: transparent;")
        layout.addWidget(self._detail_meta)

        row = QHBoxLayout()
        self._detail_play = QPushButton("\u25B6  PLAY")
        self._detail_play.setCursor(Qt.PointingHandCursor)
        self._detail_play.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']};
                border: 1px solid {COLORS['seafoam']}; padding: 10px 26px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_md']}px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['seafoam']}; color: {COLORS['void_black']}; }}
        """)
        self._detail_play.clicked.connect(self._play_current_detail)
        row.addWidget(self._detail_play)

        self._detail_fav = QPushButton("\u2606  Favorite")
        self._detail_fav.setCursor(Qt.PointingHandCursor)
        self._detail_fav.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['amber']};
                border: 1px solid {COLORS['amber']}; padding: 10px 18px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_md']}px;
            }}
            QPushButton:hover {{ background: {COLORS['amber']}; color: {COLORS['void_black']}; }}
        """)
        self._detail_fav.clicked.connect(self._toggle_detail_fav)
        row.addWidget(self._detail_fav)
        row.addStretch()
        layout.addLayout(row)

        self._detail_overview = QLabel("")
        self._detail_overview.setWordWrap(True)
        self._detail_overview.setStyleSheet(f"color: {COLORS['hd_white']}; font-size: {FONTS['size_md']}px; background: transparent;")
        layout.addWidget(self._detail_overview)
        layout.addStretch()

        self._detail_backdrop = QLabel("")
        self._detail_backdrop.setAlignment(Qt.AlignCenter)
        self._detail_backdrop.setMinimumHeight(120)
        self._detail_backdrop.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 36px; background: transparent;")
        layout.addWidget(self._detail_backdrop)

    def _make_disclaimer_box(self) -> QFrame:
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background: {glass_bg(150)}; border: 1px solid {COLORS['amber']};
                border-radius: 12px; padding: 4px;
                border-top: 1px solid {glass_sheen()};
            }}
        """)
        lay = QHBoxLayout(box)
        lay.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        lay.setSpacing(SPACING["md"])
        warn = QLabel("\u26A0")
        warn.setStyleSheet(f"color: {COLORS['amber']}; font-size: 16px; background: transparent;")
        lay.addWidget(warn)
        text = QLabel(DISCLAIMER)
        text.setWordWrap(True)
        text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_sm']}px; background: transparent;")
        lay.addWidget(text, 1)
        return box

    def _build_settings_page(self):
        layout = QVBoxLayout(self._settings_page)
        layout.setContentsMargins(SPACING["xxl"], SPACING["lg"], SPACING["xxl"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        layout.addWidget(section_header("SETTINGS"))

        # ── Local media ──
        media_title = QLabel("LOCAL MEDIA FOLDERS")
        media_title.setStyleSheet(f"color: {COLORS['seafoam']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_md']}px; font-weight: bold; background: transparent;")
        layout.addWidget(media_title)

        self._folders_list = QPlainTextEdit()
        self._folders_list.setPlaceholderText("One media folder per line, e.g.\n~/Cinema/Movies\n~/Cinema/TV")
        self._folders_list.setFixedHeight(110)
        self._folders_list.setStyleSheet(f"""
            QPlainTextEdit {{ background: {glass_bg(100)}; color: {COLORS['hd_white']};
                border: 1px solid {glass_edge()}; border-radius: 8px;
                border-top: 1px solid {glass_sheen()};
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px; }}
            QPlainTextEdit:focus {{ border-color: {COLORS['seafoam']}; }}
        """)
        self._folders_list.setPlainText("\n".join(self._settings.media_folders))
        layout.addWidget(self._folders_list)

        folder_row = QHBoxLayout()
        add_btn = QPushButton("Browse…")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(self._detail_play.styleSheet())
        add_btn.clicked.connect(self._pick_media_folder)
        folder_row.addWidget(add_btn)

        rescan_btn = self._mk_action_btn("Rescan Library", self._rescan_manual)
        folder_row.addWidget(rescan_btn)
        folder_row.addStretch()
        layout.addLayout(folder_row)

        # ── Import behavior ──
        imp_title = QLabel("IMPORT BEHAVIOR")
        imp_title.setStyleSheet(f"color: {COLORS['seafoam']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_md']}px; font-weight: bold; background: transparent; margin-top: 12px;")
        layout.addWidget(imp_title)

        self._import_move = QRadioButton("Move files into the library (frees up source space)")
        self._import_copy = QRadioButton("Copy files into the library (keep the originals)")
        for rb in (self._import_move, self._import_copy):
            rb.setStyleSheet(f"color: {COLORS['hd_white']}; font-size: {FONTS['size_sm']}px; background: transparent;")
            layout.addWidget(rb)
        self._import_move.setChecked(self._settings.import_mode != "copy")
        self._import_copy.setChecked(self._settings.import_mode == "copy")

        # ── Disclaimer ──
        disc_title = QLabel("LEGAL NOTICE")
        disc_title.setStyleSheet(f"color: {COLORS['seafoam']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_md']}px; font-weight: bold; background: transparent; margin-top: 12px;")
        layout.addWidget(disc_title)
        layout.addWidget(self._make_disclaimer_box())

        layout.addStretch()

        # ── Save ──
        save_row = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['seafoam']}; color: {COLORS['void_black']};
                border: 1px solid {COLORS['seafoam']}; border-radius: 8px;
                padding: 10px 30px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_md']}px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['seafoam_dim']}; }}
        """)
        save_btn.clicked.connect(self._save_settings)
        save_row.addWidget(save_btn)
        save_row.addStretch()
        layout.addLayout(save_row)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F5"), self).activated.connect(self._rescan_manual)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._focus_search)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self._go_back_from_detail)
        QShortcut(QKeySequence("Ctrl+I"), self).activated.connect(self._import_media)

    # ═══════════════════════════════════════════════════════════════
    #  NAVIGATION
    # ═══════════════════════════════════════════════════════════════

    def _select_sidebar(self, tag: str):
        for i in range(self._sidebar.count()):
            item = self._sidebar.item(i)
            if item.data(Qt.UserRole) == tag:
                self._sidebar.setCurrentItem(item)
                return

    def _on_sidebar(self, current, previous):
        if current is None:
            return
        tag = current.data(Qt.UserRole)
        if not tag:
            return
        if tag == "home":
            self._show_home()
        elif tag == "movies":
            self._show_movies()
        elif tag == "shows":
            self._show_shows()
        elif tag == "favorites":
            self._show_favorites()
        elif tag == "media":
            self._show_media()
        elif tag == "settings":
            self._refresh_settings_fields()
            self._stack.setCurrentWidget(self._settings_page)

    def _show_home(self):
        self._home_resume.clear()
        self._home_latest.clear()
        resume = [i for i in self._library if i.kind == "episode"][:12] or \
                 self._library[:12]
        latest = sorted(self._library, key=lambda i: i.extra.get("mtime", 0), reverse=True)[:24] or \
                 [i for i in self._library if i.kind == "movie"][:24]

        if not self._library:
            self._home_empty.setVisible(True)
            self._home_resume_label.setVisible(False)
            self._home_latest_label.setVisible(False)
            self._stack.setCurrentWidget(self._home_page)
            return

        self._home_empty.setVisible(False)
        self._home_resume_label.setVisible(True)
        self._home_latest_label.setVisible(True)
        for item in resume:
            self._bind_card(self._home_resume.add_item(item), item)
        for item in latest:
            self._bind_card(self._home_latest.add_item(item), item)
        self._stack.setCurrentWidget(self._home_page)

    def _show_movies(self):
        items = [i for i in self._library if i.kind == "movie"]
        self._fill_grid(self._movies_grid, items, self._movies_empty)
        self._stack.setCurrentWidget(self._movies_page)

    def _show_shows(self):
        items = [i for i in self._library if i.kind == "episode"]
        self._fill_grid(self._shows_grid, items, self._shows_empty)
        self._stack.setCurrentWidget(self._shows_page)

    def _show_favorites(self):
        favs = [i for i in self._library if self._settings.is_favorite(i.id)]
        self._fill_grid(self._favs_grid, favs, self._favs_empty)
        self._stack.setCurrentWidget(self._favs_page)

    def _show_media(self):
        self._fill_grid(self._media_grid, self._library, self._media_empty)
        self._stack.setCurrentWidget(self._media_page)

    def _on_search(self):
        term = self._search.text().strip()
        if not term:
            return
        self._search_grid.clear()
        self._search_empty.setVisible(False)
        self._search_grid.setVisible(True)
        local = [i for i in self._library
                 if term.lower() in i.title.lower()][:40]
        for item in local:
            card = self._search_grid.add_item(item, self._settings.is_favorite(item.id))
            self._bind_card(card, item)
        self._finish_search()
        self._stack.setCurrentWidget(self._search_page)

    def _finish_search(self):
        if not self._search_grid.cards():
            self._search_empty.setVisible(True)
            self._search_grid.setVisible(False)

    # ═══════════════════════════════════════════════════════════════
    #  CARDS
    # ═══════════════════════════════════════════════════════════════

    def _fill_grid(self, grid: MediaGrid, items: list, empty: EmptyState):
        grid.clear()
        if not items:
            empty.setVisible(True)
            grid.setVisible(False)
            return
        empty.setVisible(False)
        grid.setVisible(True)
        for item in items:
            card = grid.add_item(item, self._settings.is_favorite(item.id))
            self._bind_card(card, item)

    def _bind_card(self, card: MediaCard, item: MediaItem):
        card.clicked.connect(self._on_card_clicked)
        card.play_requested.connect(self._on_card_play)
        card.fav_toggled.connect(self._on_fav_toggled)
        card.remove_requested.connect(self._on_card_remove)

        if item.poster and os.path.isfile(item.poster):
            key = item.id
            pix = ART_CACHE.get(key)
            if pix is not None:
                card.set_poster(pix)
            else:
                pix = QPixmap(item.poster)
                if not pix.isNull():
                    pix = pix.scaled(152, 216, Qt.KeepAspectRatioByExpanding,
                                     Qt.SmoothTransformation)
                    ART_CACHE.put(key, pix)
                    card.set_poster(pix)

    # ── Card actions ──

    def _on_card_clicked(self, item: MediaItem):
        self._show_detail(item)

    def _on_card_play(self, item: MediaItem):
        self._play_item(item)

    def _on_fav_toggled(self, item: MediaItem, fav: bool):
        self._settings.toggle_favorite(item.id)
        self._settings.save(os.path.join(self._app_dir, "settings.json"))

    def _on_card_remove(self, item: MediaItem):
        self._remove_from_library(item)

    def _show_detail(self, item: MediaItem):
        self._detail_item = item
        self._detail_title.setText(item.title)
        year = f" • {item.year}" if item.year else ""
        kind = item.kind.upper()
        self._detail_meta.setText(f"{kind}{year}")
        self._detail_overview.setText(item.overview or "No synopsis available.")
        is_fav = self._settings.is_favorite(item.id)
        self._detail_fav.setText("\u2605  Favorite" if is_fav else "\u2606  Favorite")
        self._stack.setCurrentWidget(self._detail_page)

    def _go_back_from_detail(self):
        self._show_home()

    def _play_current_detail(self):
        if getattr(self, "_detail_item", None):
            self._play_item(self._detail_item)

    def _toggle_detail_fav(self):
        item = getattr(self, "_detail_item", None)
        if not item:
            return
        fav = self._settings.toggle_favorite(item.id)
        self._detail_fav.setText("\u2605  Favorite" if fav else "\u2606  Favorite")
        self._settings.save(os.path.join(self._app_dir, "settings.json"))
        self._status.setText("Added to Favorites" if fav else "Removed from Favorites")

    def _play_item(self, item: MediaItem):
        source = item.path
        if not source or not os.path.isfile(source):
            QMessageBox.information(self, "Cinema", "File not found for this item.")
            return
        self._set_busy(True, f"Starting {item.title}…")
        self._player = PlayerWindow(source, item.title)
        self._player.show()
        QTimer.singleShot(1200, lambda: self._set_busy(False, "Playing"))

    # ═══════════════════════════════════════════════════════════════
    #  MEDIA IMPORT
    # ═══════════════════════════════════════════════════════════════

    def _import_media(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Import media", os.path.expanduser("~"),
                                                _VIDEO_FILTER)
        if paths:
            self._import_paths(paths)

    def _import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Import folder",
                                                  os.path.expanduser("~"))
        if folder:
            self._import_paths([folder])

    def _import_paths(self, paths: list):
        mode = self._settings.import_mode or "move"
        verb = "Moving" if mode == "move" else "Copying"

        def work():
            imported = []
            skipped = []
            for p in paths:
                if not os.path.exists(p):
                    skipped.append(p)
                    continue
                if os.path.isdir(p):
                    dest = os.path.join(_default_library_dir(), "Movies",
                                        os.path.basename(p.rstrip(os.sep)))
                else:
                    _, dest = self._classify_dest(p)
                if os.path.normpath(dest) == os.path.normpath(p):
                    skipped.append(p)
                    continue
                self._copy_or_move(p, dest, mode)
                imported.append(dest)
            return imported, skipped

        def done(result):
            imported, skipped = result
            self._set_busy(False)
            if skipped:
                self._status.setText(f"Imported {len(imported)} file(s), skipped {len(skipped)}")
            else:
                self._status.setText(f"Imported {len(imported)} file(s) into your library")
            self._rescan_manual()

        def failed(exc):
            self._set_busy(False)
            self._status.setText("Import failed")
            QMessageBox.warning(self, "Import", f"Could not import media:\n{exc}")

        self._set_busy(True, f"{verb} media into your library…")
        self._run_bg(work, done, failed)

    def _classify_dest(self, path: str):
        """Return (library_folder, destination_path) for a video file."""
        name = os.path.basename(path)
        root, _ = os.path.splitext(name)
        if _EPISODE_RE.search(root):
            show = re.split(_EPISODE_RE, root)[0].strip(" .-_")
            show = show or "Untitled Show"
            folder = os.path.join(_default_library_dir(), "TV", show)
        else:
            folder = os.path.join(_default_library_dir(), "Movies", _clean_title(root))
        os.makedirs(folder, exist_ok=True)
        return folder, os.path.join(folder, name)

    @staticmethod
    def _copy_or_move(src: str, dest: str, mode: str):
        if mode == "move":
            shutil.move(src, dest)
        else:
            shutil.copy2(src, dest)

    def _open_library_folder(self):
        folder = _default_library_dir()
        os.makedirs(folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _remove_from_library(self, item: MediaItem):
        if not item.path:
            return
        label = item.path
        answer = QMessageBox.question(
            self, "Remove from Library",
            f"Remove “{item.title}” from your library?\n\n{label}\n\n"
            "The file will be deleted from this device.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            removed = self._delete_item_files(item)
        except Exception as exc:
            QMessageBox.warning(self, "Remove", f"Could not remove file:\n{exc}")
            return
        if item.id in self._settings.favorites:
            self._settings.favorites.remove(item.id)
        self._settings.save(os.path.join(self._app_dir, "settings.json"))
        self._rescan_manual()
        self._status.setText(f"Removed {len(removed)} file(s)")

    def _delete_item_files(self, item: MediaItem) -> list:
        removed = []
        path = item.path
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            removed.append(path)
            return removed
        if os.path.isfile(path):
            os.remove(path)
            removed.append(path)
            folder = os.path.dirname(path)
            lib = _default_library_dir()
            while folder and os.path.dirname(folder) != lib and os.path.isdir(folder) and not os.listdir(folder):
                try:
                    os.rmdir(folder)
                    folder = os.path.dirname(folder)
                except OSError:
                    break
        return removed

    # ═══════════════════════════════════════════════════════════════
    #  LIBRARY SCAN
    # ═══════════════════════════════════════════════════════════════

    def _rescan_if_stale(self):
        folders = self._settings.media_folders
        fingerprint = self._scanner.cache_fingerprint(folders)
        old = os.path.join(self._app_dir, ".fingerprint")
        try:
            with open(old) as f:
                prev = f.read()
        except OSError:
            prev = ""
        if fingerprint != prev:
            self._rescan_manual(silent=True)
        else:
            self._status.setText(f"Library ready — {len(self._library)} items")

    def _rescan_manual(self, silent: bool = False):
        folders = [f.strip() for f in self._settings.media_folders if f.strip()]
        self._set_busy(True, "Scanning media folders…")
        self._status.setText("Scanning…")

        def work():
            return self._scanner.scan(folders)

        def done(items: list):
            self._library = items
            self._scanner.save_cache(items)
            with open(os.path.join(self._app_dir, ".fingerprint"), "w") as f:
                f.write(self._scanner.cache_fingerprint(folders))
            self._set_busy(False)
            self._status.setText(f"Library updated — {len(items)} items")
            self._refresh_current_view()

        def failed(exc):
            self._set_busy(False)
            self._status.setText("Scan failed")
            QMessageBox.warning(self, "Scan", f"Could not scan library:\n{exc}")

        self._run_bg(work, done, failed)

    def _pick_media_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select media folder")
        if folder:
            current = self._folders_list.toPlainText().strip()
            lines = [line for line in current.splitlines() if line.strip()]
            if folder not in lines:
                lines.append(folder)
            self._folders_list.setPlainText("\n".join(lines))

    # ═══════════════════════════════════════════════════════════════
    #  SETTINGS
    # ═══════════════════════════════════════════════════════════════

    def _refresh_settings_fields(self):
        self._folders_list.setPlainText("\n".join(self._settings.media_folders))
        self._import_move.setChecked(self._settings.import_mode != "copy")
        self._import_copy.setChecked(self._settings.import_mode == "copy")

    def _save_settings(self):
        folders = [line.strip() for line in self._folders_list.toPlainText().splitlines() if line.strip()]
        self._settings.media_folders = folders
        self._settings.import_mode = "copy" if self._import_copy.isChecked() else "move"
        self._settings.save(os.path.join(self._app_dir, "settings.json"))
        self._status.setText("Settings saved")
        QTimer.singleShot(150, self._rescan_manual)

    def _maybe_show_disclaimer(self):
        if self._settings.disclaimer_accepted:
            return
        box = QMessageBox(self)
        box.setWindowTitle("Copyright notice")
        box.setIcon(QMessageBox.Warning)
        box.setText("One legal thing before you start")
        box.setInformativeText(
            DISCLAIMER + "\n\nBy using Cinema you agree to only watch media you "
            "own or are licensed to access.")
        box.setStandardButtons(QMessageBox.Ok)
        ok = box.exec()
        if ok:
            self._settings.disclaimer_accepted = True
            self._settings.save(os.path.join(self._app_dir, "settings.json"))

    # ═══════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _refresh_current_view(self):
        tag = self._sidebar.currentItem().data(Qt.UserRole) if self._sidebar.currentItem() else "home"
        if tag in ("home", "movies", "shows", "favorites", "media"):
            self._on_sidebar(self._sidebar.currentItem(), None)

    def _focus_search(self):
        self._search.setFocus()
        self._search.selectAll()

    def _set_busy(self, on: bool, text: str = ""):
        self._busy.setVisible(on)
        if on:
            self._busy.set_text(text)
        else:
            self._busy.set_text("")

    def _run_bg(self, work, done, failed):
        """Run a blocking function in a background QThread, then call back on the GUI thread."""
        from PySide6.QtCore import QThread

        class _Worker(QThread):
            def __init__(self, fn):
                super().__init__()
                self._fn = fn
                self.result = None

            def run(self):
                try:
                    self.result = self._fn()
                except Exception as e:
                    self.result = e

        worker = _Worker(work)
        worker.finished.connect(lambda: self._on_bg_finished(worker, done, failed))
        worker.start()
        self._bg_worker = worker

    def _on_bg_finished(self, worker, done, failed):
        result = worker.result
        worker.deleteLater()
        if isinstance(result, Exception):
            failed(result)
        else:
            done(result)

    def closeEvent(self, event):
        if self._player is not None:
            try:
                self._player.close()
            except Exception:
                pass
        event.accept()
