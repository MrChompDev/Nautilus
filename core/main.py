#!/usr/bin/env python3
"""
Nautilus OS — Core Shell (Desktop Edition)
Modern floating-glass desktop: minimal glass top bar, centered glass dock,
full-screen app launchpad grid, and the ocean wallpaper.

Launch:  py -3.13 core/main.py
Keys:    F11 / Ctrl+Alt+F  = toggle fullscreen
         Meta / Ctrl+Alt+G = app launchpad grid
         Ctrl+Space        = global search (apps / files / web)
         Ctrl+Alt+[letter] = launch an app directly
         Ctrl+Alt+Q        = shutdown Nautilus
"""

import os
import signal
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtCore import QPoint, QSize, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core import search as search_index
from core.auth import LoginDialog, get_avatar_initials
from core.icons import ensure_all_logos, get_logo, get_pixmap
from core.launcher import APP_MANIFEST, AppLauncher
from core.logger import get_logger, log_perf, log_shutdown, log_startup
from core.search_overlay import SearchOverlay
from core.theme import (
    COLORS,
    FONTS,
    SPACING,
    create_nautilus_palette,
    get_global_stylesheet,
    hex_to_rgba,
)
from core.wallpaper import generate_wallpaper

# ═══════════════════════════════════════════════════════════════
#  GLASS SURFACE TOKENS
# ═══════════════════════════════════════════════════════════════

PANEL_RADIUS = 14
DOCK_RADIUS = 18


def _glass(alpha: int = 205) -> str:
    """Translucent slate panel so the ocean wallpaper glows through."""
    return hex_to_rgba(COLORS["slate_navy"], alpha)


def _glass_dark(alpha: int = 120) -> str:
    """Darker translucent chip (metrics, date, buttons)."""
    return hex_to_rgba(COLORS["deep_navy"], alpha)


def _edge() -> str:
    """Subtle seafoam edge for glass panels."""
    return hex_to_rgba(COLORS["seafoam"], 48)


def _sheen() -> str:
    """Faint white sheen for the glass highlight line."""
    return "rgba(238, 244, 248, 26)"


# ═══════════════════════════════════════════════════════════════
#  SYSTEM TOP BAR (floating glass pill)
# ═══════════════════════════════════════════════════════════════

class TopBar(QFrame):
    """Floating glass top bar: logo, running apps, metrics, clock, controls."""

    def __init__(self, launcher: AppLauncher, username: str = "", parent=None):
        super().__init__(parent)
        self._launcher = launcher
        self._log = get_logger("UI")
        self._dragging = False
        self._drag_pos = QPoint()
        self._username = username

        self.setObjectName("topBar")
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            #topBar {{
                background: {_glass(195)};
                border: 1px solid {_edge()};
                border-top: 1px solid {_sheen()};
                border-radius: {PANEL_RADIUS}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 2, 8, 2)
        layout.setSpacing(10)

        # ── Logo + wordmark ──
        logo_icon = QLabel()
        logo_icon.setPixmap(get_logo("nautilus").pixmap(18, 18))
        layout.addWidget(logo_icon)

        logo = QLabel("NAUTILUS")
        logo.setStyleSheet(f"""
            color: {COLORS['seafoam']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(logo)

        # ── Running apps indicator ──
        self._running_container = QWidget()
        self._running_container.setStyleSheet("background: transparent;")
        self._running_layout = QHBoxLayout(self._running_container)
        self._running_layout.setContentsMargins(0, 0, 0, 0)
        self._running_layout.setSpacing(4)
        layout.addWidget(self._running_container)

        layout.addStretch()

        # ── Metrics pill ──
        metrics_pill = QFrame()
        metrics_pill.setStyleSheet(
            f"background: {_glass_dark(120)}; border-radius: 10px;"
        )
        metrics_layout = QHBoxLayout(metrics_pill)
        metrics_layout.setContentsMargins(10, 0, 10, 0)
        metrics_layout.setSpacing(0)

        self._sys_metrics = QLabel("CPU --%  RAM --%")
        self._sys_metrics.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            background: transparent;
        """)
        metrics_layout.addWidget(self._sys_metrics)
        layout.addWidget(metrics_pill)

        # ── User avatar ──
        if self._username:
            avatar_lbl = QLabel(get_avatar_initials(self._username))
            avatar_lbl.setFixedSize(24, 24)
            avatar_lbl.setAlignment(Qt.AlignCenter)
            avatar_lbl.setToolTip(self._username)
            avatar_lbl.setStyleSheet(f"""
                background: {_glass_dark(160)};
                color: {COLORS['seafoam']};
                font-family: "{FONTS['mono']}";
                font-size: 9px;
                font-weight: bold;
                border-radius: 12px;
            """)
            layout.addWidget(avatar_lbl)

        # ── Clock ──
        self._clock = QLabel("00:00")
        self._clock.setStyleSheet(f"""
            color: {COLORS['seafoam']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(self._clock)

        # ── Fullscreen toggle ──
        fs_btn = QPushButton("\u29C9")
        fs_btn.setFixedSize(30, 28)
        fs_btn.setToolTip("Toggle Fullscreen (F11)")
        fs_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['text_secondary']};
                border: 1px solid transparent; border-radius: 8px; font-size: 13px;
            }}
            QPushButton:hover {{
                background: {_glass_dark(160)}; color: {COLORS['seafoam']};
                border: 1px solid {_edge()};
            }}
        """)
        fs_btn.clicked.connect(self._on_fs_clicked)
        layout.addWidget(fs_btn)

        # ── Shutdown ──
        shutdown_btn = QPushButton("\u23FB")
        shutdown_btn.setFixedSize(30, 28)
        shutdown_btn.setToolTip("Shutdown Nautilus")
        shutdown_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['coral']};
                border: 1px solid transparent; border-radius: 8px; font-size: 13px;
            }}
            QPushButton:hover {{
                background: {hex_to_rgba(COLORS['coral'], 190)}; color: {COLORS['void_black']};
            }}
        """)
        shutdown_btn.clicked.connect(self._on_shutdown)
        layout.addWidget(shutdown_btn)

        # Timers
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick)
        self._clock_timer.start(1000)

        self._metrics_timer = QTimer(self)
        self._metrics_timer.timeout.connect(self._update_metrics)
        self._metrics_timer.start(3000)

        self._apps_timer = QTimer(self)
        self._apps_timer.timeout.connect(self._update_running_apps)
        self._apps_timer.start(2000)

        self._tick()
        self._update_metrics()

    def _tick(self):
        self._clock.setText(datetime.now().strftime("%H:%M"))

    def _update_metrics(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            self._sys_metrics.setText(f"CPU {cpu:.0f}%   RAM {mem:.0f}%")
        except Exception:
            self._sys_metrics.setText("CPU --%  RAM --%")

    def _update_running_apps(self):
        running = [aid for aid in APP_MANIFEST if self._launcher.is_running(aid)]

        while self._running_layout.count():
            item = self._running_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if running:
            self._running_container.setVisible(True)
            for aid in running:
                lbl = QLabel()
                lbl.setPixmap(get_pixmap(aid, 14))
                lbl.setToolTip(APP_MANIFEST[aid].name)
                self._running_layout.addWidget(lbl)
        else:
            self._running_container.setVisible(False)

    def _on_fs_clicked(self):
        w = self.window()
        if w:
            w._toggle_fullscreen()

    def _on_shutdown(self):
        w = self.window()
        if w:
            w._shutdown()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self.window():
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._drag_pos = event.globalPosition().toPoint()
            w = self.window()
            if not w.isFullScreen():
                w.move(w.pos() + delta)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False


# ═══════════════════════════════════════════════════════════════
#  DESKTOP WALLPAPER (clean canvas + floating widgets)
# ═══════════════════════════════════════════════════════════════

class DesktopWallpaper(QWidget):
    """The desktop canvas with the ocean wallpaper, a glass clock card,
    and the right-click menu."""

    def __init__(self, launcher: AppLauncher, username: str = "", parent=None):
        super().__init__(parent)
        self._launcher = launcher
        self._wallpaper_path = None
        self._username = username
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

        # Generate the wallpaper at the current screen resolution
        try:
            screen = QApplication.primaryScreen()
            size = screen.size() if screen else None
            self._wallpaper_path = generate_wallpaper(
                size.width() if size else 1920,
                size.height() if size else 1080,
            )
        except Exception:
            self._wallpaper_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 58, 28, 28)
        layout.setSpacing(0)

        # ── Glass clock / greeting card (top-left) ──
        card = QFrame()
        card.setStyleSheet(f"""
            background: {_glass(170)};
            border: 1px solid {_edge()};
            border-top: 1px solid {_sheen()};
            border-radius: 18px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(4)

        self._time_lbl = QLabel("00:00")
        self._time_lbl.setStyleSheet(f"""
            color: {COLORS['hd_white']};
            font-family: "{FONTS['mono']}";
            font-size: 34px;
            font-weight: bold;
            background: transparent;
        """)
        card_layout.addWidget(self._time_lbl)

        self._date_lbl = QLabel("")
        self._date_lbl.setStyleSheet(f"""
            color: {COLORS['seafoam']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            letter-spacing: 2px;
            background: transparent;
        """)
        card_layout.addWidget(self._date_lbl)

        greeting = QLabel(self._greeting())
        greeting.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_sm']}px;
            background: transparent;
        """)
        card_layout.addWidget(greeting)

        layout.addWidget(card, 0, Qt.AlignLeft | Qt.AlignTop)
        layout.addStretch(1)

        # ── Bottom row: hint (left) + watermark (right) ──
        bottom = QHBoxLayout()
        bottom.setSpacing(SPACING["md"])

        hint = QLabel("Right-click desktop  ·  Ctrl+Space search  ·  Meta app grid")
        hint.setStyleSheet(f"""
            color: {hex_to_rgba(COLORS['text_muted'], 180)};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            background: transparent;
        """)
        bottom.addWidget(hint, 0, Qt.AlignBottom | Qt.AlignLeft)

        bottom.addStretch(1)

        wm = QHBoxLayout()
        wm.setSpacing(6)
        wm_logo = QLabel()
        wm_logo.setPixmap(get_logo("nautilus").pixmap(16, 16))
        wm.addWidget(wm_logo)
        wm_txt = QLabel("NAUTILUS OS")
        wm_txt.setStyleSheet(f"""
            color: {hex_to_rgba(COLORS['hd_white'], 90)};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            letter-spacing: 3px;
            background: transparent;
        """)
        wm.addWidget(wm_txt)
        bottom.addLayout(wm)

        layout.addLayout(bottom)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _greeting(self) -> str:
        hour = datetime.now().hour
        if hour < 5:
            part = "UP LATE"
        elif hour < 12:
            part = "GOOD MORNING"
        elif hour < 18:
            part = "GOOD AFTERNOON"
        else:
            part = "GOOD EVENING"
        who = f", {self._username.upper()}" if self._username else ""
        return f"{part}{who}"

    def _tick_clock(self):
        now = datetime.now()
        self._time_lbl.setText(now.strftime("%H:%M"))
        self._date_lbl.setText(now.strftime("%A, %d %B %Y").upper())

    def _on_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {_glass(220)};
                color: {COLORS['hd_white']};
                border: 1px solid {_edge()};
                border-radius: 10px;
                padding: 6px 0;
            }}
            QMenu::item {{
                padding: 6px 22px 6px 14px;
                border-radius: 6px;
                margin: 1px 6px;
            }}
            QMenu::item:selected {{
                background-color: {hex_to_rgba(COLORS['seafoam_deep'], 200)};
                color: {COLORS['seafoam']};
            }}
            QMenu::separator {{
                height: 1px; background: {_edge()}; margin: 4px 12px;
            }}
        """)

        launch_menu = menu.addMenu("\U0001f680  Launch App")
        for app_id, entry in APP_MANIFEST.items():
            action = launch_menu.addAction(f"  {entry.name}")
            action.setIcon(get_logo(app_id))
            action.triggered.connect(lambda checked, aid=app_id: self._launcher.launch(aid))

        menu.addSeparator()

        menu.addAction("\U0001f4c1  Harbor File Manager").triggered.connect(
            lambda: self._launcher.launch("harbor")
        )
        menu.addAction("\u2328  Tide Terminal").triggered.connect(
            lambda: self._launcher.launch("tide")
        )
        menu.addAction("\U0001f680  App Grid").triggered.connect(
            lambda: self._toggle_launchpad()
        )
        menu.addAction("\u2699  Anchor Settings").triggered.connect(
            lambda: self._launcher.launch("anchor")
        )

        menu.addSeparator()
        menu.addAction("\U0001f5d1  Terminate All Apps").triggered.connect(
            self._launcher.terminate_all
        )
        menu.addAction("\u23fb  Shutdown Nautilus").triggered.connect(
            lambda: w._shutdown() if (w := self.window()) else None
        )

        menu.exec(self.mapToGlobal(pos))

    def _toggle_launchpad(self):
        w = self.window()
        if w:
            w._toggle_launchpad()

    def paintEvent(self, event):
        """Paint the generated wallpaper as the desktop background."""
        painter = QPainter(self)

        if self._wallpaper_path and os.path.exists(self._wallpaper_path):
            pm = QPixmap(self._wallpaper_path)
            if not pm.isNull():
                painter.drawPixmap(self.rect(), pm)
            else:
                painter.fillRect(self.rect(), QColor(COLORS["abyss_navy"]))
        else:
            painter.fillRect(self.rect(), QColor(COLORS["abyss_navy"]))

        painter.end()


# ═══════════════════════════════════════════════════════════════
#  DOCK BUTTON (icon tile with running dot)
# ═══════════════════════════════════════════════════════════════

class DockButton(QToolButton):
    """Modern icon-only dock tile with a running-status dot."""

    def __init__(self, app_id: str, entry, launcher: AppLauncher, parent=None):
        super().__init__(parent)
        self._app_id = app_id
        self._entry = entry
        self._launcher = launcher

        self.setIcon(get_logo(app_id))
        self.setIconSize(QSize(28, 28))
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setFixedSize(52, 52)
        self.setToolTip(f"{entry.name}\n{entry.shortcut}\n{entry.description}")
        self.setCursor(Qt.PointingHandCursor)

        self._dot = QLabel(self)
        self._dot.setFixedSize(6, 6)
        self._dot.setStyleSheet(
            f"background: {COLORS['seafoam']}; border-radius: 3px;"
        )
        self._dot.hide()

        self._apply_style(False)
        self.clicked.connect(lambda: self._launcher.launch(self._app_id))

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_status)
        self._timer.start(2000)

    def _apply_style(self, running: bool):
        if running:
            self.setStyleSheet(f"""
                QToolButton {{
                    background: {hex_to_rgba(COLORS['seafoam_deep'], 130)};
                    border: 1px solid {hex_to_rgba(COLORS['seafoam'], 140)};
                    border-radius: 14px;
                }}
                QToolButton:hover {{
                    background: {hex_to_rgba(COLORS['seafoam_deep'], 190)};
                    border: 1px solid {COLORS['seafoam']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QToolButton {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 14px;
                }}
                QToolButton:hover {{
                    background: {_sheen()};
                    border: 1px solid {hex_to_rgba(COLORS['seafoam'], 70)};
                }}
                QToolButton:pressed {{
                    background: {hex_to_rgba(COLORS['seafoam_deep'], 130)};
                }}
            """)

    def _check_status(self):
        running = self._launcher.is_running(self._app_id)
        self._apply_style(running)
        self._dot.setVisible(running)

    def resizeEvent(self, event):
        self._dot.move(
            (self.width() - self._dot.width()) // 2,
            self.height() - self._dot.height() - 4,
        )
        super().resizeEvent(event)


# ═══════════════════════════════════════════════════════════════
#  SYSTEM DOCK (floating glass, centered)
# ═══════════════════════════════════════════════════════════════

class SystemDock(QFrame):
    """Centered floating glass dock: launchpad button, app tiles, date chip."""

    def __init__(self, launcher: AppLauncher, on_open_launchpad, parent=None):
        super().__init__(parent)
        self._launcher = launcher
        self._dragging = False
        self._drag_pos = QPoint()

        self.setObjectName("systemDock")
        self.setFixedHeight(66)
        self.setStyleSheet(f"""
            #systemDock {{
                background: {_glass(190)};
                border: 1px solid {_edge()};
                border-top: 1px solid {_sheen()};
                border-radius: {DOCK_RADIUS}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # ── Launchpad toggle ──
        lp_btn = QPushButton("\u229e")
        lp_btn.setFixedSize(52, 52)
        lp_btn.setToolTip("App Grid (Meta)")
        lp_btn.setCursor(Qt.PointingHandCursor)
        lp_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_glass_dark(140)};
                color: {COLORS['seafoam']};
                border: 1px solid {_edge()};
                border-radius: 14px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background: {hex_to_rgba(COLORS['seafoam_deep'], 170)};
                border: 1px solid {hex_to_rgba(COLORS['seafoam'], 140)};
            }}
        """)
        lp_btn.clicked.connect(on_open_launchpad)
        layout.addWidget(lp_btn)

        layout.addWidget(self._separator())

        # ── App tiles ──
        for app_id, entry in APP_MANIFEST.items():
            layout.addWidget(DockButton(app_id, entry, launcher))

        layout.addWidget(self._separator())

        # ── Date / time chip ──
        chip = QFrame()
        chip.setStyleSheet(
            f"background: {_glass_dark(140)}; border-radius: 12px;"
        )
        chip_layout = QVBoxLayout(chip)
        chip_layout.setContentsMargins(12, 2, 12, 2)
        chip_layout.setSpacing(0)
        chip_layout.setAlignment(Qt.AlignCenter)

        self._chip_time = QLabel("00:00")
        self._chip_time.setAlignment(Qt.AlignCenter)
        self._chip_time.setStyleSheet(f"""
            color: {COLORS['seafoam']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            font-weight: bold;
            background: transparent;
        """)
        chip_layout.addWidget(self._chip_time)

        self._chip_date = QLabel("")
        self._chip_date.setAlignment(Qt.AlignCenter)
        self._chip_date.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            background: transparent;
        """)
        chip_layout.addWidget(self._chip_date)
        layout.addWidget(chip)

        self._chip_timer = QTimer(self)
        self._chip_timer.timeout.connect(self._tick_chip)
        self._chip_timer.start(30000)
        self._tick_chip()

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setFixedSize(1, 36)
        sep.setStyleSheet(f"background: {_sheen()};")
        return sep

    def _tick_chip(self):
        now = datetime.now()
        self._chip_time.setText(now.strftime("%H:%M"))
        self._chip_date.setText(now.strftime("%d %b %Y").upper())

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self.window():
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._drag_pos = event.globalPosition().toPoint()
            w = self.window()
            if not w.isFullScreen():
                w.move(w.pos() + delta)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False


# ═══════════════════════════════════════════════════════════════
#  LAUNCHPAD (full-screen app grid)
# ═══════════════════════════════════════════════════════════════

class LaunchpadOverlay(QFrame):
    """Full-screen dimmed overlay with a searchable app grid."""

    def __init__(self, launcher: AppLauncher, parent=None):
        super().__init__(parent)
        self._launcher = launcher
        self._tiles = {}

        self.setObjectName("launchpad")
        self.setStyleSheet(
            "QFrame#launchpad { background: rgba(2, 6, 10, 215); border: none; }"
        )
        self.hide()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        panel = QFrame()
        panel.setStyleSheet(f"""
            background: {_glass(235)};
            border: 1px solid {_edge()};
            border-top: 1px solid {_sheen()};
            border-radius: 22px;
        """)
        panel.setMinimumWidth(760)
        panel.setMaximumWidth(880)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(28, 22, 28, 26)
        panel_layout.setSpacing(16)

        title = QLabel("APPLICATIONS")
        title.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            letter-spacing: 4px;
            background: transparent;
        """)
        panel_layout.addWidget(title, 0, Qt.AlignHCenter)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter applications\u2026")
        self._search.setFixedHeight(40)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {_glass_dark(150)};
                color: {COLORS['hd_white']};
                border: 1px solid {_edge()};
                border-radius: 12px;
                padding: 0 14px;
                font-family: "{FONTS['ui']}";
                font-size: {FONTS['size_md']}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['seafoam']};
            }}
        """)
        self._search.textChanged.connect(self._rebuild)
        panel_layout.addWidget(self._search)

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(10)
        panel_layout.addWidget(self._grid_host, 0, Qt.AlignHCenter)

        outer.addWidget(panel)

        QShortcut(QKeySequence("Escape"), self).activated.connect(self.hide)

        self._build_tiles()

    # ── construction ──

    def _build_tiles(self):
        for app_id, entry in APP_MANIFEST.items():
            tile = QToolButton()
            tile.setIcon(get_logo(app_id))
            tile.setIconSize(QSize(46, 46))
            tile.setText(entry.name.split()[0][:10])
            tile.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tile.setFixedSize(128, 116)
            tile.setCursor(Qt.PointingHandCursor)
            tile.setToolTip(f"{entry.name}\n{entry.description}")
            tile.setStyleSheet(f"""
                QToolButton {{
                    background: {_glass_dark(150)};
                    color: {COLORS['text_secondary']};
                    border: 1px solid transparent;
                    border-radius: 16px;
                    font-family: "{FONTS['mono']}";
                    font-size: {FONTS['size_xs']}px;
                }}
                QToolButton:hover {{
                    background: {hex_to_rgba(COLORS['seafoam_deep'], 170)};
                    color: {COLORS['hd_white']};
                    border: 1px solid {hex_to_rgba(COLORS['seafoam'], 120)};
                }}
                QToolButton:pressed {{
                    background: {hex_to_rgba(COLORS['seafoam_deep'], 220)};
                }}
            """)
            tile.clicked.connect(lambda checked=False, aid=app_id: self._launch(aid))
            self._tiles[app_id] = tile

    # ── behaviour ──

    def open_launchpad(self):
        parent = self.parentWidget()
        if parent:
            self.setGeometry(0, 0, parent.width(), parent.height())
        self._search.clear()
        self._rebuild("")
        self.show()
        self.raise_()
        self._search.setFocus()

    def _launch(self, app_id: str):
        self.hide()
        self._launcher.launch(app_id)

    def _rebuild(self, query: str):
        query = query.strip()
        if query:
            matched = {r["app_id"] for r in search_index.match_apps(query, APP_MANIFEST)}
        else:
            matched = set(APP_MANIFEST.keys())

        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.hide()

        for index, app_id in enumerate(APP_MANIFEST):
            if app_id not in matched:
                continue
            col = index % 5
            row = index // 5
            self._grid.addWidget(self._tiles[app_id], row, col)
            self._tiles[app_id].show()

        self._grid_host.adjustSize()


# ═══════════════════════════════════════════════════════════════
#  CORE DESKTOP SHELL
# ═══════════════════════════════════════════════════════════════

class NautilusShell(QMainWindow):
    """Nautilus OS Desktop Shell — modern floating-glass desktop environment."""

    def __init__(self, username: str = ""):
        super().__init__()
        self._log = get_logger("CORE")
        self._launcher = AppLauncher(PROJECT_ROOT)
        self._fullscreen = True
        self._username = username

        self.setWindowTitle("Nautilus OS")
        self.setMinimumSize(1024, 640)

        # Set Nautilus logo as window icon
        self.setWindowIcon(get_logo("nautilus"))

        # Start in pseudo-fullscreen (maximized, frameless)
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint
        )
        self.showMaximized()

        self._setup_ui()
        self._setup_shortcuts()
        self._setup_tray()
        self._setup_launcher_hooks()

        self._log.info("Desktop shell initialized")

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Top bar (floating glass, full width with side gaps) ──
        top_area = QWidget()
        top_area.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_area)
        top_layout.setContentsMargins(12, 10, 12, 0)
        top_layout.setSpacing(0)
        self._top_bar = TopBar(self._launcher, self._username)
        top_layout.addWidget(self._top_bar, 1)
        main_layout.addWidget(top_area)

        # ── Desktop ──
        self._desktop = DesktopWallpaper(self._launcher, self._username)
        main_layout.addWidget(self._desktop, 1)

        # ── Dock (floating glass, centered) ──
        dock_area = QWidget()
        dock_area.setStyleSheet("background: transparent;")
        dock_layout = QHBoxLayout(dock_area)
        dock_layout.setContentsMargins(12, 10, 12, 12)
        dock_layout.setSpacing(0)
        self._dock = SystemDock(self._launcher, self._toggle_launchpad)
        dock_layout.addWidget(self._dock, 0, Qt.AlignHCenter | Qt.AlignBottom)
        main_layout.addWidget(dock_area)

        # ── Launchpad overlay ──
        self._launchpad = LaunchpadOverlay(self._launcher)
        self._launchpad.setParent(central)

        # ── Search overlay ──
        self._search_overlay = SearchOverlay(self._launcher)
        self._search_overlay.setParent(central)
        self._search_overlay.adjustSize()

    def _setup_shortcuts(self):
        # App launch shortcuts
        for app_id, entry in APP_MANIFEST.items():
            shortcut = QShortcut(QKeySequence(entry.shortcut), self)
            shortcut.activated.connect(lambda aid=app_id: self._launcher.launch(aid))

        # Fullscreen toggle
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+Alt+F"), self).activated.connect(self._toggle_fullscreen)

        # Shutdown
        QShortcut(QKeySequence("Ctrl+Alt+Q"), self).activated.connect(self._shutdown)

        # Minimize to tray
        QShortcut(QKeySequence("Ctrl+Alt+Esc"), self).activated.connect(self.showMinimized)

        # Global search
        QShortcut(QKeySequence("Ctrl+Space"), self).activated.connect(
            self._show_search_overlay
        )
        QShortcut(QKeySequence("Ctrl+Alt+Space"), self).activated.connect(
            self._show_search_overlay
        )

        # Launchpad (Meta / Super key + printable fallback)
        QShortcut(QKeySequence(Qt.Key_Meta), self).activated.connect(
            self._toggle_launchpad
        )
        QShortcut(QKeySequence("Ctrl+Alt+G"), self).activated.connect(
            self._toggle_launchpad
        )

    def _show_search_overlay(self):
        if self._search_overlay.isVisible():
            self._search_overlay.hide()
        else:
            self._search_overlay.show_overlay()
            self._search_overlay.move(
                (self.width() - self._search_overlay.width()) // 2,
                (self.height() - self._search_overlay.height()) // 3,
            )

    def _toggle_launchpad(self):
        if self._launchpad.isVisible():
            self._launchpad.hide()
        else:
            self._launchpad.open_launchpad()

    def _setup_tray(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = self._build_tray()
        else:
            self._tray = None
            self._log.warn("System tray not available")

    def _build_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(self)

        tray.setIcon(get_logo("nautilus"))
        tray.setToolTip("Nautilus OS")

        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {_glass(225)};
                color: {COLORS['hd_white']};
                border: 1px solid {_edge()};
                border-radius: 10px;
                padding: 6px 0;
            }}
            QMenu::item {{
                padding: 6px 22px 6px 14px;
                border-radius: 6px;
                margin: 1px 6px;
            }}
            QMenu::item:selected {{
                background-color: {hex_to_rgba(COLORS['seafoam_deep'], 200)};
                color: {COLORS['seafoam']};
            }}
            QMenu::separator {{
                height: 1px; background: {_edge()}; margin: 4px 12px;
            }}
        """)

        apps_menu = menu.addMenu("\U0001f680  Launch App")
        for app_id, entry in APP_MANIFEST.items():
            action = apps_menu.addAction(f"  {entry.name}")
            action.setIcon(get_logo(app_id))
            action.triggered.connect(lambda checked, aid=app_id: self._launcher.launch(aid))

        apps_menu.addSeparator()
        apps_menu.addAction("\u23fb  Terminate All").triggered.connect(self._launcher.terminate_all)

        menu.addSeparator()
        menu.addAction("\U0001f5a5  Show Desktop").triggered.connect(self._show_desktop)
        menu.addAction("\U0001f680  App Grid").triggered.connect(self._toggle_launchpad)
        menu.addAction("\u23fb  Shutdown").triggered.connect(self._shutdown)

        tray.setContextMenu(menu)
        tray.activated.connect(lambda reason: self._show_desktop()
                               if reason == QSystemTrayIcon.DoubleClick else None)
        tray.show()
        return tray

    def _setup_launcher_hooks(self):
        self._launcher.on_launch(lambda app_id, proc: self._log.info(
            f"App launched: {APP_MANIFEST[app_id].name} (PID {proc.pid})"
        ))
        self._launcher.on_exit(lambda app_id: self._log.info(
            f"App exited: {APP_MANIFEST[app_id].name}"
        ))

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self._log.info("Entering fullscreen mode")
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.showFullScreen()
        else:
            self._log.info("Exiting fullscreen mode")
            self.setWindowFlags(
                Qt.Window |
                Qt.WindowSystemMenuHint |
                Qt.WindowMinimizeButtonHint |
                Qt.WindowMaximizeButtonHint |
                Qt.WindowCloseButtonHint
            )
            self.showNormal()
            self.resize(1280, 800)

    def _show_desktop(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _shutdown(self):
        reply = QMessageBox.question(
            self, "Shutdown Nautilus",
            "Terminate all running applications and shut down Nautilus OS?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._log.info("Shutdown initiated by user")
            self._launcher.terminate_all()
            log_shutdown()
            QApplication.instance().quit()

    def closeEvent(self, event):
        if self._tray and self._tray.isVisible():
            self._log.info("Minimizing to system tray")
            self.hide()
            event.ignore()
        else:
            self._shutdown()
            if not self.isVisible():
                event.accept()
            else:
                event.ignore()


def main():
    log_startup()
    t0 = datetime.now()

    # Create QApplication first - this is required for Qt operations
    app = QApplication(sys.argv)
    app.setApplicationName("Nautilus OS")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Nautilus")

    app.setPalette(create_nautilus_palette())
    app.setStyleSheet(get_global_stylesheet())

    font = QFont()
    font.setFamilies([FONTS["ui"], FONTS["mono"], FONTS["mono_fallback"], FONTS["mono_fallback2"]])
    font.setPointSize(FONTS["size_md"])
    app.setFont(font)

    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    signal.signal(signal.SIGTERM, lambda sig, frame: app.quit())

    # Pre-generate all app logos (after QApplication is created)
    ensure_all_logos()

    # ── Login Dialog ──
    login = LoginDialog()
    if login.exec() != LoginDialog.Accepted:
        sys.exit(0)

    username = login.get_logged_in_user()
    _log = get_logger("SYSTEM")
    _log.info(f"User logged in: {username}")

    shell = NautilusShell(username=username or "User")
    shell.show()

    elapsed = (datetime.now() - t0).total_seconds() * 1000
    log_perf("shell_boot", elapsed)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
