#!/usr/bin/env python3
"""
Tide — Nautilus GPU-Accelerated Terminal Emulator
Multi-tabbed terminal container running the Tide internal shell
(a pure-Python interpreter — no external $SHELL / cmd.exe required).

All command execution runs in background threads — zero UI blocking.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtCore import (
    QMutex,
    QMutexLocker,
    QThread,
)
from PySide6.QtCore import (
    Signal as QSignal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QPalette,
    QShortcut,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.Tide.shell import InternalShell

try:
    from core.theme import (
        COLORS,
        FONTS,
        SPACING,
        create_nautilus_palette,
        get_global_stylesheet,
        glass_bg,
        glass_bg_dark,
        glass_edge,
        glass_sheen,
    )
except ImportError:
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
        "seafoam_glow": "#00F2C240", "seafoam_deep": "#004D40", "coral": "#FF7F50",
        "coral_dim": "#CC6640", "amber": "#FFA502", "emerald": "#00C853",
        "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8", "text_muted": "#506070",
        "text_bright": "#FFFFFF", "border": "#152D44", "border_active": "#00F2C2",
        "border_dim": "#0A1A2A", "surface_hover": "#132A40", "surface_pressed": "#0A1A2A",
        "surface_selected": "#1A3352", "terminal_bg": "#030810", "terminal_fg": "#00F2C2",
        "terminal_dim": "#007A6640", "scrollbar_bg": "#050D14",
        "scrollbar_handle": "#1A3352", "scrollbar_hover": "#254565",
        "tab_active": "#0E2238", "tab_inactive": "#050D14", "tab_hover": "#0A1628",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11,
             "size_md": 12, "size_lg": 13, "size_xl": 14, "size_xxl": 16, "size_title": 20}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "xxl": 24, "xxxl": 32}

    def get_global_stylesheet():
        return ""
    def create_nautilus_palette():
        return QPalette()
    def hex_to_rgba(h, a=255):
        v = h.lstrip("#")
        return f"rgba({int(v[0:2],16)},{int(v[2:4],16)},{int(v[4:6],16)},{a})"
    def glass_bg(a=180): return hex_to_rgba(COLORS["slate_navy"], a)
    def glass_bg_dark(a=140): return hex_to_rgba(COLORS["deep_navy"], a)
    def glass_edge(a=48): return hex_to_rgba(COLORS["seafoam"], a)
    def glass_sheen(): return "rgba(238, 244, 248, 26)"


# Output styles -> theme color keys
_STYLE_COLORS = {
    "out": "hd_white",
    "err": "coral",
    "sys": "seafoam",
    "dim": "text_muted",
    "accent": "seafoam",
}


# ═══════════════════════════════════════════════════════════════
#  COMMAND WORKER — runs the internal shell in a background thread
# ═══════════════════════════════════════════════════════════════

class CommandWorker(QThread):
    """Executes a command line through the shared InternalShell. Zero UI blocking."""

    output_ready = QSignal(str, str)
    command_finished = QSignal(int)
    session_exit = QSignal()

    def __init__(self, shell: InternalShell, cmd: str, parent=None):
        super().__init__(parent)
        self._shell = shell
        self._cmd = cmd
        self._mutex = QMutex()

    def run(self):
        try:
            code = self._shell.execute(self._cmd, on_output=self._on_output)
            self.command_finished.emit(code)
            if self._shell.exit_requested:
                self.session_exit.emit()
        except Exception as e:
            self._on_output(str(e) + "\n", "err")
            self.command_finished.emit(1)

    def _on_output(self, text: str, style: str):
        self.output_ready.emit(text, style)

    def kill(self):
        with QMutexLocker(self._mutex):
            self._shell.request_abort()


# ═══════════════════════════════════════════════════════════════
#  TERMINAL SESSION — one shell per tab
# ═══════════════════════════════════════════════════════════════

class TerminalSession(QWidget):
    """A single terminal session backed by an InternalShell."""

    cwd_changed = QSignal(str)
    exit_requested = QSignal()

    def __init__(self, shell: InternalShell = None, parent=None):
        super().__init__(parent)
        self._shell = shell or InternalShell()
        self._cwd = self._shell.cwd
        self._worker = None
        self._history_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        # Output display
        self._display = QTextEdit()
        self._display.setReadOnly(True)
        self._display.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(3, 8, 16, 210);
                color: {COLORS['terminal_fg']};
                border: 1px solid {glass_edge(40)};
                border-radius: 12px;
                font-family: "{FONTS['mono']}", "Consolas", monospace;
                font-size: {FONTS['size_sm']}px;
                padding: 6px;
                selection-background-color: {COLORS['seafoam_deep']};
                selection-color: {COLORS['terminal_fg']};
            }}
        """)
        layout.addWidget(self._display, 1)

        # Input line
        input_layout = QHBoxLayout()
        input_layout.setSpacing(0)

        self._prompt = QLabel("\u276f ")
        self._prompt.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['seafoam']};
                font-family: "{FONTS['mono']}", "Consolas";
                font-size: {FONTS['size_sm']}px;
                font-weight: bold;
                padding: 4px 8px;
                background: {glass_bg_dark(160)};
                border-radius: 8px 0 0 8px;
            }}
        """)
        input_layout.addWidget(self._prompt)

        self._input = QLineEdit()
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {glass_bg_dark(160)};
                color: {COLORS['hd_white']};
                border: 1px solid {glass_edge(40)};
                border-left: none;
                border-radius: 0 8px 8px 0;
                font-family: "{FONTS['mono']}", "Consolas", monospace;
                font-size: {FONTS['size_sm']}px;
                padding: 4px 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['seafoam']};
                border-left: none;
            }}
        """)
        self._input.returnPressed.connect(self._execute)
        input_layout.addWidget(self._input, 1)

        layout.addLayout(input_layout)

        # Welcome
        self._print_welcome()

    def _print_welcome(self):
        self._append_output(
            f"\u2554{'=' * 42}\u2557\n"
            f"\u2551   \U0001f30a  TIDE TERMINAL  v2.0              \u2551\n"
            f"\u2551   Shell: internal (pure Python)    \u2551\n"
            f"\u2551   CWD:   {self._cwd[:32]:<32}\u2551\n"
            f"\u255a{'=' * 42}\u255d\n\n",
            "accent",
        )

    # -- execution --------------------------------------------------------

    def _execute(self):
        cmd = self._input.text().strip()
        if not cmd:
            return

        self._history_index = len(self._shell.history)
        self._append_output(f"\n\u276f {cmd}\n", "accent")
        self._input.clear()

        self._input.setEnabled(False)
        self._prompt.setText("\u23f3 ")

        self._worker = CommandWorker(self._shell, cmd)
        self._worker.output_ready.connect(
            lambda text, style: self._append_output(text, style)
        )
        self._worker.command_finished.connect(self._on_command_done)
        self._worker.session_exit.connect(self.exit_requested.emit)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_command_done(self, exit_code: int):
        if exit_code not in (0, 130):
            self._append_output(f"[exit code: {exit_code}]\n", "dim")

    def _on_worker_finished(self):
        self._input.setEnabled(True)
        self._prompt.setText("\u276f ")
        if self._shell.cwd != self._cwd:
            self._cwd = self._shell.cwd
            self.cwd_changed.emit(self._cwd)
        self._input.setFocus()
        self._worker = None

    def _abort_command(self):
        """Kill the running command (Ctrl+C)."""
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.kill()
            self._worker.wait(1000)
            self._append_output("\n[^C]\n", "coral")

    # -- output ------------------------------------------------------------

    def _append_output(self, text: str, style: str = "out"):
        if style == "clear":
            self._display.clear()
            return
        color = COLORS.get(_STYLE_COLORS.get(style, "hd_white"), COLORS["hd_white"])
        cursor = self._display.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text, fmt)
        self._display.setTextCursor(cursor)
        self._display.ensureCursorVisible()

    # -- history ------------------------------------------------------------

    def history_up(self):
        hist = self._shell.history
        if hist and self._history_index > 0:
            self._history_index -= 1
            self._input.setText(hist[self._history_index])

    def history_down(self):
        hist = self._shell.history
        if self._history_index < len(hist) - 1:
            self._history_index += 1
            self._input.setText(hist[self._history_index])
        else:
            self._history_index = len(hist)
            self._input.clear()

    def get_cwd(self) -> str:
        return self._cwd

    def focus_input(self):
        self._input.setFocus()


# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class TideWindow(QMainWindow):
    """Tide — Nautilus GPU-Accelerated Terminal Emulator."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tide \u2014 Terminal")
        self.setMinimumSize(800, 500)
        self.resize(1000, 650)
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"QWidget {{ background: {glass_bg(180)}; }}")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        main_layout.setSpacing(SPACING["sm"])

        # Title bar
        title_bar = QHBoxLayout()
        title = QLabel("\u2328  TIDE  //  Terminal Emulator")
        title.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_lg']}px; font-weight: bold; letter-spacing: 2px;
            background: transparent;
        """)
        title_bar.addWidget(title)
        title_bar.addStretch()

        self._new_tab_btn = QPushButton("+")
        self._new_tab_btn.setFixedSize(28, 24)
        self._new_tab_btn.setStyleSheet(f"""
            QPushButton {{
                background: {glass_bg(140)};
                color: {COLORS['seafoam']};
                border: 1px solid {glass_edge(60)};
                border-radius: 8px;
                font-size: 16px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {glass_bg(200)}; border-color: {glass_edge(100)}; }}
        """)
        self._new_tab_btn.clicked.connect(self._add_tab)
        title_bar.addWidget(self._new_tab_btn)
        main_layout.addLayout(title_bar)

        # Tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._close_tab)
        self._tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {glass_bg_dark(180)};
                border: 1px solid {glass_edge()};
                border-radius: 12px;
            }}
            QTabBar::tab {{
                background: {glass_bg_dark(120)};
                color: {COLORS['text_secondary']};
                padding: 5px 14px;
                border: 1px solid transparent;
                border-bottom: 2px solid transparent;
                border-radius: 8px;
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_xs']}px;
                min-width: 60px;
                height: 26px;
            }}
            QTabBar::tab:selected {{
                background: {glass_bg(180)};
                color: {COLORS['seafoam']};
                border-bottom: 2px solid {COLORS['seafoam']};
                border-color: {glass_edge()};
            }}
            QTabBar::tab:hover:!selected {{
                background: {glass_bg(150)};
                color: {COLORS['hd_white']};
                border-color: {glass_edge(30)};
            }}
        """)

        self._add_tab("shell")
        main_layout.addWidget(self._tab_widget, 1)

        # Status
        status = QLabel(
            "internal shell \u00b7 Ctrl+T:new  Ctrl+W:close  Ctrl+Tab:next  "
            "Up/Down:history  Ctrl+C:abort  Ctrl+L:clear"
        )
        status.setStyleSheet(f"""
            color: {COLORS['text_muted']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px; padding-top: 4px;
            border-top: 1px solid {glass_edge()};
            background: transparent;
        """)
        main_layout.addWidget(status)

    def _add_tab(self, name: str = None):
        name = name or f"term-{self._tab_widget.count() + 1}"
        session = TerminalSession()
        idx = self._tab_widget.addTab(session, name)
        self._tab_widget.setCurrentIndex(idx)
        session.focus_input()
        session.cwd_changed.connect(lambda cwd, idx=idx: self._on_cwd_changed(cwd, idx))
        session.exit_requested.connect(
            lambda s=session: self._close_tab(self._tab_widget.indexOf(s))
        )

    def _close_tab(self, index: int):
        if self._tab_widget.count() > 1:
            widget = self._tab_widget.widget(index)
            if isinstance(widget, TerminalSession):
                widget._abort_command()
            self._tab_widget.removeTab(index)

    def _on_cwd_changed(self, cwd: str, tab_index: int):
        self._tab_widget.setTabText(tab_index, os.path.basename(cwd) or cwd)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(lambda: self._add_tab())
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(
            lambda: self._close_tab(self._tab_widget.currentIndex())
        )
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(
            lambda: self._tab_widget.setCurrentIndex(
                (self._tab_widget.currentIndex() + 1) % self._tab_widget.count()
            )
        )
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(
            lambda: self._tab_widget.setCurrentIndex(
                (self._tab_widget.currentIndex() - 1) % self._tab_widget.count()
            )
        )
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._clear_current)

        # Ctrl+C to abort current command
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self._abort_current)

    def _clear_current(self):
        widget = self._tab_widget.currentWidget()
        if isinstance(widget, TerminalSession):
            widget._display.clear()

    def _abort_current(self):
        widget = self._tab_widget.currentWidget()
        if isinstance(widget, TerminalSession):
            widget._abort_command()

    def closeEvent(self, event):
        for i in range(self._tab_widget.count()):
            widget = self._tab_widget.widget(i)
            if isinstance(widget, TerminalSession):
                widget._abort_command()
        event.accept()


# ═══════════════════════════════════════════════════════════════

def main():
    try:
        from core.logger import get_logger
        log = get_logger("APP")
        log.info("Tide Terminal starting")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Tide")
    app.setOrganizationName("Nautilus")

    try:
        from core.icons import get_logo
        app.setWindowIcon(get_logo("tide"))
    except Exception:
        pass

    app.setPalette(create_nautilus_palette())
    app.setStyleSheet(get_global_stylesheet())

    font = QFont()
    font.setFamilies([FONTS["mono"], "Consolas", "Courier New"])
    font.setPointSize(FONTS["size_sm"])
    app.setFont(font)

    window = TideWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
