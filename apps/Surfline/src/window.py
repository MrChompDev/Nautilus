"""
Surfline Browser - Main Window
The core browser interface with tabs, URL bar, and developer tools.
"""
import os
import sys

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from apps.Surfline.src.dialogs import (
    ImportDialog,
    PasswordManagerDialog,
    SettingsDialog,
)
from apps.Surfline.src.icons import ensure_icons, icon_path
from apps.Surfline.src.json_viewer import StructuredDataViewer
from apps.Surfline.src.reef_shield import ReefShieldFilter
from apps.Surfline.src.terminal import TerminalWidget
from apps.Surfline.src.theme import COLORS, FONTS, get_stylesheet
from apps.Surfline.src.tide_sync import TideSyncManager

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class SurflineUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, filter_engine: ReefShieldFilter, parent=None):
        super().__init__(parent)
        self.filter_engine = filter_engine

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        if self.filter_engine.should_block(url):
            info.block(True)


class SurflineWebPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)

    def javaScriptConsoleMessage(self, level, message, line, source):
        pass

    def certificateError(self, error):
        return True


class SurflineTab:
    def __init__(self, url="about:blank", title="New Tab"):
        self.url = url
        self.title = title
        self.web_view = None
        self.history = [url]
        self.history_index = 0


class ProfileDialog(QDialog):
    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self.setWindowTitle("TideSync Profile Manager")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("TIDESYNC PROFILE MANAGER")
        header.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_lg']}px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 8px 0;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        layout.addWidget(header)

        self.profile_list = QComboBox()
        self.profile_list.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                padding: 6px 8px;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_md']}px;
            }}
            QComboBox:focus {{
                border: 1px solid {COLORS['accent']};
            }}
        """)
        self.refresh_list()
        layout.addWidget(self.profile_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        create_btn = QPushButton("Create New")
        create_btn.clicked.connect(self.create_profile)
        btn_row.addWidget(create_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_profile)
        btn_row.addWidget(delete_btn)

        activate_btn = QPushButton("Activate")
        activate_btn.clicked.connect(self.activate_profile)
        btn_row.addWidget(activate_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def refresh_list(self):
        self.profile_list.clear()
        for name in self.sync_manager.get_profile_names():
            self.profile_list.addItem(name)

    def create_profile(self):
        name, ok = QInputDialog.getText(
            self, "Create Profile", "Profile name:",
            QLineEdit.Normal, ""
        )
        if ok and name.strip():
            self.sync_manager.create_profile(name.strip())
            self.refresh_list()

    def delete_profile(self):
        name = self.profile_list.currentText()
        if name:
            reply = QMessageBox.question(
                self, "Delete Profile",
                f"Delete profile '{name}'? This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.sync_manager.delete_profile(name)
                self.refresh_list()

    def activate_profile(self):
        name = self.profile_list.currentText()
        if name:
            self.sync_manager.set_active(name)
            QMessageBox.information(
                self, "Profile Activated",
                f"Active profile set to '{name}'"
            )


class HeaderViewerDialog(QDialog):
    def __init__(self, headers_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Request/Response Headers")
        self.setMinimumSize(600, 400)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        layout = QVBoxLayout(self)

        header = QLabel("HTTP HEADERS")
        header.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_lg']}px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 8px 0;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        layout.addWidget(header)

        text = QTextEdit()
        text.setPlainText(headers_text)
        text.setReadOnly(True)
        text.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['terminal_bg']};
                color: {COLORS['terminal_text']};
                border: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 8px;
                selection-background-color: {COLORS['selection']};
            }}
        """)
        layout.addWidget(text)

        close_btn = QPushButton("Close (Esc)")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


# SettingsDialog is now imported from src.dialogs


class SurflineWindow(QMainWindow):
    def __init__(self, initial_url: str = None):
        super().__init__()
        ensure_icons()

        self.setWindowTitle("Surfline Browser")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 900)

        self.reef_shield = ReefShieldFilter()
        self.reef_interceptor = SurflineUrlRequestInterceptor(self.reef_shield, self)
        self.sync_manager = TideSyncManager()

        self.settings = self.sync_manager.get_all_settings()

        self.tabs = []
        self.tab_web_views = {}
        self.current_tab_index = -1

        self._setup_web_engine_profile()
        self.setup_ui()
        self.apply_theme()
        self.setup_shortcuts()
        self.setup_statusbar()

        self.add_new_tab(initial_url or "https://www.google.com", "New Tab")

    def _setup_web_engine_profile(self):
        profile_name = "surfline_default"
        self.web_profile = QWebEngineProfile(profile_name, self)
        self.web_profile.setHttpUserAgent(
            "Surfline/1.0 (Developer Browser; ChompOS)"
        )
        self.web_profile.setUrlRequestInterceptor(self.reef_interceptor)
        self.web_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        storage = os.path.join(BASE_DIR, "assets", "profiles", "cache")
        os.makedirs(storage, exist_ok=True)
        self.web_profile.setCachePath(storage)
        self.web_profile.setPersistentStoragePath(storage)

        settings = self.web_profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,
                              self.settings.get("javascript_enabled", True))
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled,
            self.settings.get("smooth_scrolling", True)
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True
        )
        settings.setFontFamily(QWebEngineSettings.FontFamily.FixedFont, "JetBrains Mono")
        settings.setFontSize(QWebEngineSettings.FontSize.MinimumFontSize, 10)
        settings.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize,
                             self.settings.get("font_size", 12))
        settings.setFontSize(QWebEngineSettings.FontSize.MinimumLogicalFontSize, 10)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toolbar = self._create_toolbar()
        main_layout.addWidget(self.toolbar)

        self.tab_bar = QTabWidget()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {COLORS['bg_primary']};
            }}
            QTabBar {{
                background: {COLORS['bg_secondary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTabBar::tab {{
                background: {COLORS['tab_inactive']};
                color: {COLORS['text_secondary']};
                padding: 4px 12px 4px 12px;
                margin-right: 1px;
                border: none;
                border-bottom: 2px solid transparent;
                min-width: 100px;
                max-width: 220px;
                height: 28px;
                font-size: {FONTS['size_sm']}px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['tab_active']};
                color: {COLORS['accent']};
                border-bottom: 2px solid {COLORS['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {COLORS['tab_hover']};
                color: {COLORS['text_primary']};
            }}
        """)

        self.content_splitter = QSplitter(Qt.Vertical)
        self.content_splitter.addWidget(self.tab_bar)

        self.bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(self.bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {COLORS['bg_primary']};
                border-top: 1px solid {COLORS['border']};
            }}
            QTabBar::tab {{
                background: {COLORS['tab_inactive']};
                color: {COLORS['text_secondary']};
                padding: 3px 12px;
                border: none;
                border-bottom: 2px solid transparent;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['tab_active']};
                color: {COLORS['accent']};
                border-bottom: 2px solid {COLORS['accent']};
            }}
        """)

        self.terminal = TerminalWidget()
        self.bottom_tabs.addTab(self.terminal, "TERMINAL")

        self.json_viewer = StructuredDataViewer()
        self.bottom_tabs.addTab(self.json_viewer, "DATA VIEWER")

        bottom_layout.addWidget(self.bottom_tabs)
        self.bottom_panel.setMaximumHeight(350)
        self.bottom_panel.setMinimumHeight(100)
        self.content_splitter.addWidget(self.bottom_panel)
        self.content_splitter.setSizes([600, 200])
        self.content_splitter.setHandleWidth(2)

        main_layout.addWidget(self.content_splitter)

    def _create_toolbar(self):
        toolbar = QWidget()
        toolbar.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_secondary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        toolbar.setMinimumHeight(36)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        btn_style = f"""
            QToolButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                padding: 3px 6px;
                font-size: {FONTS['size_lg']}px;
            }}
            QToolButton:hover {{
                color: {COLORS['accent']};
                background: {COLORS['bg_elevated']};
            }}
            QToolButton:pressed {{
                color: {COLORS['accent']};
                background: {COLORS['accent_darker']}40;
            }}
        """

        self.btn_back = QToolButton()
        self.btn_back.setIcon(self._load_icon("back"))
        self.btn_back.setToolTip("Back (Alt+Left)")
        self.btn_back.setStyleSheet(btn_style)
        self.btn_back.clicked.connect(self.navigate_back)
        layout.addWidget(self.btn_back)

        self.btn_forward = QToolButton()
        self.btn_forward.setIcon(self._load_icon("forward"))
        self.btn_forward.setToolTip("Forward (Alt+Right)")
        self.btn_forward.setStyleSheet(btn_style)
        self.btn_forward.clicked.connect(self.navigate_forward)
        layout.addWidget(self.btn_forward)

        self.btn_reload = QToolButton()
        self.btn_reload.setIcon(self._load_icon("reload"))
        self.btn_reload.setToolTip("Reload (F5)")
        self.btn_reload.setStyleSheet(btn_style)
        self.btn_reload.clicked.connect(self.reload_page)
        layout.addWidget(self.btn_reload)

        self.btn_home = QToolButton()
        self.btn_home.setIcon(self._load_icon("home"))
        self.btn_home.setToolTip("Home")
        self.btn_home.setStyleSheet(btn_style)
        self.btn_home.clicked.connect(self.go_home)
        layout.addWidget(self.btn_home)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("URL / Search")
        self.url_bar.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                padding: 3px 10px;
                selection-background-color: {COLORS['selection']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['accent']};
            }}
        """)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        layout.addWidget(self.url_bar, 1)

        self.btn_go = QToolButton()
        self.btn_go.setText("GO")
        self.btn_go.setStyleSheet(f"""
            QToolButton {{
                background: {COLORS['accent_darker']};
                color: {COLORS['bg_primary']};
                border: none;
                padding: 3px 12px;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background: {COLORS['accent']};
            }}
        """)
        self.btn_go.clicked.connect(self.navigate_to_url)
        layout.addWidget(self.btn_go)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep1)

        self.btn_new_tab = QToolButton()
        self.btn_new_tab.setIcon(self._load_icon("new_tab"))
        self.btn_new_tab.setToolTip("New Tab (Ctrl+T)")
        self.btn_new_tab.setStyleSheet(btn_style)
        self.btn_new_tab.clicked.connect(lambda: self.add_new_tab("about:blank", "New Tab"))
        layout.addWidget(self.btn_new_tab)

        self.btn_shield = QToolButton()
        self.btn_shield.setIcon(self._load_icon("shield"))
        self.btn_shield.setToolTip("Reef Shield: Toggle Ad Blocking")
        self.btn_shield.setStyleSheet(btn_style)
        self.btn_shield.clicked.connect(self.toggle_reef_shield)
        layout.addWidget(self.btn_shield)

        self.shield_label = QLabel()
        self.shield_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
            }}
        """)
        layout.addWidget(self.shield_label)
        self._update_shield_label()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep2)

        self.btn_profile = QToolButton()
        self.btn_profile.setIcon(self._load_icon("profile"))
        self.btn_profile.setToolTip("TideSync Profiles")
        self.btn_profile.setStyleSheet(btn_style)
        self.btn_profile.clicked.connect(self.open_profile_manager)
        layout.addWidget(self.btn_profile)

        self.btn_terminal = QToolButton()
        self.btn_terminal.setIcon(self._load_icon("terminal"))
        self.btn_terminal.setToolTip("Toggle Terminal (Ctrl+`)")
        self.btn_terminal.setStyleSheet(btn_style)
        self.btn_terminal.clicked.connect(self.toggle_terminal)
        layout.addWidget(self.btn_terminal)

        self.btn_find = QToolButton()
        self.btn_find.setIcon(self._load_icon("find"))
        self.btn_find.setToolTip("Find in Page (Ctrl+F)")
        self.btn_find.setStyleSheet(btn_style)
        self.btn_find.clicked.connect(self.find_in_page)
        layout.addWidget(self.btn_find)

        self.btn_settings = QToolButton()
        self.btn_settings.setIcon(self._load_icon("settings"))
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.setStyleSheet(btn_style)
        self.btn_settings.clicked.connect(self.open_settings)
        layout.addWidget(self.btn_settings)

        self.btn_bookmark = QToolButton()
        self.btn_bookmark.setIcon(self._load_icon("bookmark"))
        self.btn_bookmark.setToolTip("Bookmark Current Page")
        self.btn_bookmark.setStyleSheet(btn_style)
        self.btn_bookmark.clicked.connect(self.bookmark_page)
        layout.addWidget(self.btn_bookmark)

        self.btn_menu = QToolButton()
        self.btn_menu.setIcon(self._load_icon("menu"))
        self.btn_menu.setToolTip("Menu")
        self.btn_menu.setStyleSheet(btn_style)
        self.btn_menu.clicked.connect(self.show_menu)
        layout.addWidget(self.btn_menu)

        return toolbar

    def _load_icon(self, name):
        path = icon_path(name)
        if os.path.exists(path):
            return QIcon(path)
        return QIcon()

    def apply_theme(self):
        self.setStyleSheet(get_stylesheet())

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self, self.add_new_tab_shortcut)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self.prev_tab)
        QShortcut(QKeySequence("F5"), self, self.reload_page)
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload_page)
        QShortcut(QKeySequence("Alt+Left"), self, self.navigate_back)
        QShortcut(QKeySequence("Alt+Right"), self, self.navigate_forward)
        QShortcut(QKeySequence("Alt+Home"), self, self.go_home)
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_url_bar)
        QShortcut(QKeySequence("F6"), self, self.focus_url_bar)
        QShortcut(QKeySequence("Ctrl+F"), self, self.find_in_page)
        QShortcut(QKeySequence("Escape"), self, self.stop_loading)
        QShortcut(QKeySequence("F12"), self, self.toggle_devtools)
        QShortcut(QKeySequence("Ctrl+Shift+H"), self, self.show_headers)
        QShortcut(QKeySequence("Ctrl+`"), self, self.toggle_terminal)
        QShortcut(QKeySequence("Ctrl+Shift+J"), self, self.toggle_bottom_panel)
        QShortcut(QKeySequence("Ctrl+D"), self, self.bookmark_page)
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.switch_tab(0))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self.switch_tab(1))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self.switch_tab(2))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self.switch_tab(3))
        QShortcut(QKeySequence("Ctrl+5"), self, lambda: self.switch_tab(4))
        QShortcut(QKeySequence("Ctrl+6"), self, lambda: self.switch_tab(5))
        QShortcut(QKeySequence("Ctrl+7"), self, lambda: self.switch_tab(6))
        QShortcut(QKeySequence("Ctrl+8"), self, lambda: self.switch_tab(7))
        QShortcut(QKeySequence("Ctrl+9"), self, lambda: self.switch_tab(-1))
        QShortcut(QKeySequence("Ctrl+Shift+Delete"), self, self.clear_data)

    def setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.setStyleSheet(f"""
            QStatusBar {{
                background: {COLORS['bg_secondary']};
                color: {COLORS['text_secondary']};
                border-top: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
            }}
        """)

        self.status_label = QLabel("Ready")
        self.statusbar.addWidget(self.status_label, 1)

        self.depth_label = QLabel()
        self.depth_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_dim']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
                padding: 0 8px;
                border-left: 1px solid {COLORS['border']};
            }}
        """)
        self.statusbar.addPermanentWidget(self.depth_label)

        self.metrics_label = QLabel()
        self.metrics_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
                padding: 0 8px;
            }}
        """)
        self.statusbar.addPermanentWidget(self.metrics_label)

        self.load_progress = QProgressBar()
        self.load_progress.setMaximumWidth(120)
        self.load_progress.setMaximumHeight(2)
        self.load_progress.setTextVisible(False)
        self.load_progress.hide()
        self.statusbar.addPermanentWidget(self.load_progress)

        self.shield_status = QLabel()
        self.shield_status.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
                padding: 0 8px;
                border-left: 1px solid {COLORS['border']};
            }}
        """)
        self.statusbar.addPermanentWidget(self.shield_status)

        self.profile_label = QLabel()
        self.profile_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
                padding: 0 8px;
                border-left: 1px solid {COLORS['border']};
            }}
        """)
        self.statusbar.addPermanentWidget(self.profile_label)
        self._update_profile_label()
        self._update_shield_label()

        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self._update_metrics)
        self.metrics_timer.start(2000)
        self._update_metrics()

    def _update_metrics(self):
        import random
        mem = self._get_process_memory()
        tabs = len(self.tabs)
        blocked = self.reef_shield.get_stats()["total_blocked"]
        depth = random.randint(3200, 4100)
        pressure = round(depth * 0.101325, 0)
        self.metrics_label.setText(
            f"MEM: {mem}MB | TABS: {tabs} | BLOCKED: {blocked}"
        )
        self.depth_label.setText(
            f"{depth}m | {int(pressure)} ATM"
        )
        self.shield_status.setText(
            f"[{'ON' if self.reef_shield.enabled else 'OFF'}]"
        )

    def _get_process_memory(self):
        try:
            import ctypes
            if sys.platform == "win32":
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetCurrentProcess()
                mem_info = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetProcessWorkingSetSize(
                    ctypes.c_void_p(handle),
                    ctypes.byref(ctypes.c_ulonglong()),
                    ctypes.byref(mem_info)
                )
                return f"{mem_info.value // (1024 * 1024)}"
        except Exception:
            pass
        return "N/A"

    def _update_shield_label(self):
        stats = self.reef_shield.get_stats()
        if stats["enabled"]:
            self.shield_label.setText(f"REEF: {stats['rule_count']} RULES")
            self.shield_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['accent']};
                    font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                    font-size: {FONTS['size_xs']}px;
                }}
            """)
        else:
            self.shield_label.setText("REEF: OFFLINE")
            self.shield_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text_muted']};
                    font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                    font-size: {FONTS['size_xs']}px;
                }}
            """)

    def _update_profile_label(self):
        active = self.sync_manager.active_profile_name
        self.profile_label.setText(f"[{active or 'none'}]")

    def add_new_tab(self, url="about:blank", title="New Tab"):
        tab = SurflineTab(url, title)
        web_view = QWebEngineView()

        page = SurflineWebPage(self.web_profile, web_view)
        web_view.setPage(page)

        page.loadStarted.connect(
            lambda: self.on_page_load_started(tab)
        )
        page.loadProgress.connect(
            lambda p: self.on_page_load_progress(p)
        )
        page.loadFinished.connect(
            lambda ok: self.on_page_load_finished(tab, ok)
        )
        page.titleChanged.connect(
            lambda t: self.on_title_changed(tab, t)
        )
        page.urlChanged.connect(
            lambda u: self.on_url_changed(tab, u)
        )

        tab.web_view = web_view
        self.tabs.append(tab)

        idx = self.tab_bar.count()
        self.tab_bar.addTab(web_view, title)
        self.tab_bar.setCurrentIndex(idx)
        self.tab_web_views[id(web_view)] = tab

        if url and url != "about:blank":
            web_view.setUrl(QUrl(url))
        else:
            self._set_new_tab_page(web_view)

        self.url_bar.setText(url)

        zoom = self.settings.get("default_zoom", 100) / 100.0
        web_view.setZoomFactor(zoom)

        return tab

    def _set_new_tab_page(self, web_view):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: #060E1A;
            color: #D8E2EC;
            font-family: "JetBrains Mono", "Consolas", monospace;
            height: 100vh;
            overflow: hidden;
            position: relative;
        }

        /* Deep ocean gradient base */
        .ocean-bg {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background:
                radial-gradient(ellipse at 20% 80%, #00F2C208 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, #004D4008 0%, transparent 50%),
                radial-gradient(ellipse at 50% 100%, #0A1E33 0%, #060E1A 60%);
            z-index: 0;
        }

        /* Particle field - floating bioluminescence */
        .particles {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: 1;
            overflow: hidden;
        }

        .particle {
            position: absolute;
            width: 2px;
            height: 2px;
            background: #00F2C2;
            border-radius: 0;
            opacity: 0;
            animation: drift linear infinite;
        }

        .particle:nth-child(1) { left: 8%; animation-duration: 18s; animation-delay: 0s; }
        .particle:nth-child(2) { left: 15%; animation-duration: 22s; animation-delay: 2s; width: 1px; height: 1px; }
        .particle:nth-child(3) { left: 25%; animation-duration: 16s; animation-delay: 4s; }
        .particle:nth-child(4) { left: 35%; animation-duration: 24s; animation-delay: 1s; width: 3px; height: 3px; }
        .particle:nth-child(5) { left: 45%; animation-duration: 20s; animation-delay: 3s; }
        .particle:nth-child(6) { left: 55%; animation-duration: 19s; animation-delay: 5s; width: 1px; height: 1px; }
        .particle:nth-child(7) { left: 65%; animation-duration: 21s; animation-delay: 0.5s; }
        .particle:nth-child(8) { left: 75%; animation-duration: 17s; animation-delay: 2.5s; width: 3px; height: 3px; }
        .particle:nth-child(9) { left: 82%; animation-duration: 23s; animation-delay: 1.5s; }
        .particle:nth-child(10) { left: 92%; animation-duration: 15s; animation-delay: 4.5s; width: 1px; height: 1px; }
        .particle:nth-child(11) { left: 5%; animation-duration: 26s; animation-delay: 6s; }
        .particle:nth-child(12) { left: 50%; animation-duration: 20s; animation-delay: 7s; width: 2px; height: 2px; }
        .particle:nth-child(13) { left: 30%; animation-duration: 25s; animation-delay: 3.5s; }
        .particle:nth-child(14) { left: 70%; animation-duration: 18s; animation-delay: 5.5s; width: 1px; height: 1px; }
        .particle:nth-child(15) { left: 88%; animation-duration: 22s; animation-delay: 8s; }

        @keyframes drift {
            0% { transform: translateY(110vh) translateX(0); opacity: 0; }
            10% { opacity: 0.6; }
            50% { opacity: 0.3; }
            90% { opacity: 0.5; }
            100% { transform: translateY(-10vh) translateX(40px); opacity: 0; }
        }

        /* Depth lines - sonar grid */
        .depth-grid {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: 1;
            opacity: 0.04;
        }

        .depth-line {
            position: absolute;
            left: 0; right: 0;
            height: 1px;
            background: #00F2C2;
        }

        .depth-line:nth-child(1) { top: 20%; }
        .depth-line:nth-child(2) { top: 40%; }
        .depth-line:nth-child(3) { top: 60%; }
        .depth-line:nth-child(4) { top: 80%; }

        .depth-line-v {
            position: absolute;
            top: 0; bottom: 0;
            width: 1px;
            background: #00F2C2;
        }

        .depth-line-v:nth-child(5) { left: 20%; }
        .depth-line-v:nth-child(6) { left: 40%; }
        .depth-line-v:nth-child(7) { left: 60%; }
        .depth-line-v:nth-child(8) { left: 80%; }

        /* Wave layers */
        .waves {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 200px;
            z-index: 1;
        }

        .wave {
            position: absolute;
            bottom: 0;
            left: -5%;
            width: 110%;
            height: 60px;
            background: #00F2C206;
            animation: wave-move linear infinite;
        }

        .wave:nth-child(1) {
            animation-duration: 8s;
            height: 40px;
            background: #00F2C204;
        }

        .wave:nth-child(2) {
            animation-duration: 12s;
            animation-delay: -3s;
            height: 30px;
            background: #00F2C206;
            bottom: 10px;
        }

        .wave:nth-child(3) {
            animation-duration: 15s;
            animation-delay: -6s;
            height: 50px;
            background: #00F2C203;
            bottom: 5px;
        }

        @keyframes wave-move {
            0% { transform: translateX(-5%); }
            50% { transform: translateX(5%); }
            100% { transform: translateX(-5%); }
        }

        /* Main content */
        .content {
            position: relative;
            z-index: 10;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }

        .logo-area {
            text-align: center;
            margin-bottom: 48px;
        }

        .logo-mark {
            display: inline-block;
            position: relative;
            margin-bottom: 16px;
        }

        .logo-mark svg {
            filter: drop-shadow(0 0 20px #00F2C230);
        }

        .logo-text {
            font-size: 42px;
            font-weight: 700;
            color: #00F2C2;
            letter-spacing: 14px;
            text-shadow: 0 0 40px #00F2C220;
            margin-bottom: 6px;
        }

        .logo-tagline {
            color: #4A5D6E;
            font-size: 10px;
            letter-spacing: 6px;
            text-transform: uppercase;
        }

        /* Depth meter */
        .depth-meter {
            position: fixed;
            right: 24px;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            z-index: 10;
        }

        .depth-label {
            color: #4A5D6E;
            font-size: 9px;
            letter-spacing: 2px;
            writing-mode: vertical-rl;
            text-orientation: mixed;
            margin-bottom: 8px;
        }

        .depth-bar {
            width: 2px;
            height: 120px;
            background: #152D44;
            position: relative;
        }

        .depth-fill {
            position: absolute;
            bottom: 0;
            width: 100%;
            background: #00F2C2;
            animation: depth-pulse 4s ease-in-out infinite;
            box-shadow: 0 0 8px #00F2C240;
        }

        @keyframes depth-pulse {
            0%, 100% { height: 30%; }
            50% { height: 70%; }
        }

        .depth-value {
            color: #00F2C2;
            font-size: 9px;
            font-family: "JetBrains Mono", monospace;
            margin-top: 8px;
        }

        /* Search */
        .search-container {
            width: 520px;
            max-width: 80vw;
            position: relative;
        }

        .search-input {
            width: 100%;
            background: #081A2E;
            color: #D8E2EC;
            border: 1px solid #152D44;
            padding: 12px 16px 12px 40px;
            font-family: "JetBrains Mono", "Consolas", monospace;
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .search-input:focus {
            border-color: #00F2C2;
            box-shadow: 0 0 0 1px #00F2C220, 0 0 30px #00F2C208;
        }

        .search-input::placeholder {
            color: #4A5D6E;
        }

        .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: #4A5D6E;
        }

        .search-input:focus ~ .search-icon {
            color: #00F2C2;
        }

        /* Quick links */
        .links {
            margin-top: 32px;
            display: flex;
            gap: 2px;
        }

        .link {
            color: #7A8FA0;
            text-decoration: none;
            font-size: 10px;
            padding: 6px 14px;
            border: 1px solid #152D44;
            background: #0A162808;
            letter-spacing: 1px;
            transition: all 0.15s;
        }

        .link:hover {
            border-color: #00F2C2;
            color: #00F2C2;
            background: #00F2C208;
            box-shadow: 0 0 12px #00F2C210;
        }

        /* Stats bar */
        .stats {
            position: fixed;
            bottom: 16px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 24px;
            z-index: 10;
        }

        .stat {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #4A5D6E;
            font-size: 9px;
            letter-spacing: 1px;
        }

        .stat-dot {
            width: 4px;
            height: 4px;
            background: #00F2C2;
            box-shadow: 0 0 6px #00F2C260;
        }

        .stat-dot.dormant {
            background: #152D44;
            box-shadow: none;
        }

        /* Horizon line */
        .horizon {
            position: fixed;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg,
                transparent 0%,
                #00F2C208 20%,
                #00F2C210 50%,
                #00F2C208 80%,
                transparent 100%);
            z-index: 1;
        }
        </style>
        </head>
        <body>

        <div class="ocean-bg"></div>

        <div class="depth-grid">
            <div class="depth-line"></div>
            <div class="depth-line"></div>
            <div class="depth-line"></div>
            <div class="depth-line"></div>
            <div class="depth-line-v"></div>
            <div class="depth-line-v"></div>
            <div class="depth-line-v"></div>
            <div class="depth-line-v"></div>
        </div>

        <div class="horizon"></div>

        <div class="particles">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
        </div>

        <div class="waves">
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
        </div>

        <div class="content">
            <div class="logo-area">
                <div class="logo-mark">
                    <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                        <rect x="2" y="2" width="44" height="44" stroke="#00F2C2" stroke-width="1.5" fill="none" opacity="0.3"/>
                        <path d="M10 30 Q16 18 24 24 Q32 30 38 20" stroke="#00F2C2" stroke-width="2" fill="none"/>
                        <path d="M10 34 Q16 22 24 28 Q32 34 38 24" stroke="#00F2C2" stroke-width="1" fill="none" opacity="0.3"/>
                        <circle cx="24" cy="24" r="3" fill="#00F2C2" opacity="0.6"/>
                        <line x1="24" y1="10" x2="24" y2="18" stroke="#00F2C2" stroke-width="1" opacity="0.4"/>
                        <line x1="24" y1="30" x2="24" y2="38" stroke="#00F2C2" stroke-width="1" opacity="0.4"/>
                        <line x1="10" y1="24" x2="18" y2="24" stroke="#00F2C2" stroke-width="1" opacity="0.4"/>
                        <line x1="30" y1="24" x2="38" y2="24" stroke="#00F2C2" stroke-width="1" opacity="0.4"/>
                    </svg>
                </div>
                <div class="logo-text">SURFLINE</div>
                <div class="logo-tagline">Built for coders, by coders</div>
            </div>

            <div class="search-container">
                <form action="https://www.google.com/search" method="GET">
                    <input class="search-input" type="text" name="q" placeholder="Search or enter URL..." autofocus />
                    <div class="search-icon">
                        <svg width="16" height="16" viewBox="0 0 16 16">
                            <circle cx="6" cy="6" r="4" stroke="currentColor" stroke-width="1.5" fill="none"/>
                            <line x1="9" y1="9" x2="14" y2="14" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                    </div>
                </form>
            </div>

            <div class="links">
                <a class="link" href="https://github.com">GITHUB</a>
                <a class="link" href="https://stackoverflow.com">STACKOVERFLOW</a>
                <a class="link" href="https://news.ycombinator.com">HACKER NEWS</a>
                <a class="link" href="https://developer.mozilla.org">MDN</a>
                <a class="link" href="https://reddit.com/r/programming">R/PROG</a>
            </div>
        </div>

        <div class="depth-meter">
            <div class="depth-label">DEPTH</div>
            <div class="depth-bar">
                <div class="depth-fill"></div>
            </div>
            <div class="depth-value">3847m</div>
        </div>

        <div class="stats">
            <div class="stat"><div class="stat-dot"></div> REEF SHIELD</div>
            <div class="stat"><div class="stat-dot"></div> V8 ENGINE</div>
            <div class="stat"><div class="stat-dot"></div> CHROMIUM</div>
            <div class="stat"><div class="stat-dot dormant"></div> TIDESYNC</div>
        </div>

        </body>
        </html>
        """
        web_view.setHtml(html, QUrl("about:blank"))

    def add_new_tab_shortcut(self):
        self.add_new_tab("about:blank", "New Tab")

    def close_tab(self, index):
        if len(self.tabs) <= 1:
            return
        tab = self.tabs[index]
        if tab.web_view:
            self.tab_web_views.pop(id(tab.web_view), None)
            tab.web_view.deleteLater()
        self.tab_bar.removeTab(index)
        del self.tabs[index]
        if self.current_tab_index >= len(self.tabs):
            self.current_tab_index = len(self.tabs) - 1

    def close_current_tab(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0:
            self.close_tab(idx)

    def on_tab_changed(self, index):
        if index < 0 or index >= len(self.tabs):
            return
        self.current_tab_index = index
        tab = self.tabs[index]
        if tab.web_view:
            page = tab.web_view.page()
            if page and page.url():
                self.url_bar.setText(page.url().toString())

    def switch_tab(self, index):
        if index == -1:
            index = self.tab_bar.count() - 1
        if 0 <= index < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(index)

    def next_tab(self):
        idx = (self.tab_bar.currentIndex() + 1) % self.tab_bar.count()
        self.tab_bar.setCurrentIndex(idx)

    def prev_tab(self):
        idx = (self.tab_bar.currentIndex() - 1) % self.tab_bar.count()
        self.tab_bar.setCurrentIndex(idx)

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if text.startswith(("http://", "https://", "file://", "about:")):
            url = text
        elif "." in text and " " not in text:
            url = "https://" + text
        else:
            search_url = self.settings.get("search_url", "https://www.google.com/search?q={}")
            url = search_url.replace("{}", text.replace(" ", "+"))

        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view:
                tab.web_view.setUrl(QUrl(url))

    def navigate_back(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view and tab.web_view.page().history().canGoBack():
                tab.web_view.page().history().back()

    def navigate_forward(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view and tab.web_view.page().history().canGoForward():
                tab.web_view.page().history().forward()

    def reload_page(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view:
                tab.web_view.reload()

    def stop_loading(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view:
                tab.web_view.stop()

    def go_home(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view:
                homepage = self.settings.get("homepage", "about:blank")
                if homepage == "about:blank":
                    self._set_new_tab_page(tab.web_view)
                else:
                    tab.web_view.setUrl(QUrl(homepage))

    def focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def find_in_page(self):
        text, ok = QInputDialog.getText(
            self, "Find in Page", "Text to find:"
        )
        if ok and text:
            idx = self.tab_bar.currentIndex()
            if idx >= 0 and idx < len(self.tabs):
                tab = self.tabs[idx]
                if tab.web_view:
                    page = tab.web_view.page()
                    page.findText(text)

    def toggle_reef_shield(self):
        enabled = self.reef_shield.toggle()
        self._update_shield_label()
        self.status_label.setText(
            f"Reef Shield: {'ENABLED' if enabled else 'DISABLED'}"
        )

    def toggle_terminal(self):
        if self.bottom_panel.isVisible():
            self.bottom_panel.hide()
        else:
            self.bottom_panel.show()
            self.terminal.input.setFocus()

    def toggle_bottom_panel(self):
        self.toggle_terminal()

    def toggle_devtools(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view:
                page = tab.web_view.page()
                if not hasattr(self, '_devtools_view') or self._devtools_view is None:
                    from PySide6.QtWebEngineWidgets import QWebEngineView
                    self._devtools_view = QWebEngineView()
                    self._devtools_view.setWindowTitle("Surfline DevTools")
                    self._devtools_view.setMinimumSize(600, 400)
                    self._devtools_view.setStyleSheet(f"""
                        QMainWindow {{
                            background: {COLORS['bg_primary']};
                        }}
                    """)
                    page.setDevToolsPage(self._devtools_view.page())
                    self._devtools_view.show()
                else:
                    self._devtools_view.close()
                    self._devtools_view = None

    def show_headers(self):
        idx = self.tab_bar.currentIndex()
        if idx < 0 or idx >= len(self.tabs):
            return
        tab = self.tabs[idx]
        if not tab.web_view:
            return
        page = tab.web_view.page()
        url = page.url().toString() if page.url() else "N/A"

        headers_text = "REQUEST HEADERS\n"
        headers_text += "=" * 60 + "\n"
        headers_text += f"URL: {url}\n"
        headers_text += "User-Agent: Surfline/1.0 (Developer Browser; ChompOS)\n"
        headers_text += "Accept: text/html,application/xhtml+xml\n"
        headers_text += "Accept-Language: en-US,en;q=0.9\n"
        headers_text += "Accept-Encoding: gzip, deflate, br\n"
        headers_text += "Connection: keep-alive\n"
        headers_text += "Sec-Fetch-Dest: document\n"
        headers_text += "Sec-Fetch-Mode: navigate\n"
        headers_text += "Sec-Fetch-Site: none\n"
        headers_text += "Sec-Fetch-User: ?1\n"
        headers_text += "Upgrade-Insecure-Requests: 1\n"
        headers_text += "\n"
        headers_text += "RESPONSE HEADERS\n"
        headers_text += "=" * 60 + "\n"
        headers_text += "(Headers are intercepted at network layer)\n"
        headers_text += f"Reef Shield Rules Active: {self.reef_shield.get_stats()['rule_count']}\n"
        headers_text += f"Requests Blocked: {self.reef_shield.get_stats()['total_blocked']}\n"

        dialog = HeaderViewerDialog(headers_text, self)
        dialog.exec()

    def open_profile_manager(self):
        dialog = ProfileDialog(self.sync_manager, self)
        dialog.exec()
        self._update_profile_label()

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted:
            self.settings.update(dialog.result_settings)
            self.sync_manager.update_settings(self.settings)
            if hasattr(dialog, '_pending_export'):
                etype, path = dialog._pending_export
                active = self.sync_manager.active_profile_name
                if active:
                    if etype == "bookmarks":
                        self.sync_manager.export_bookmarks(active, path)
                        self.status_label.setText(f"Bookmarks exported to {path}")
                    elif etype == "passwords_json":
                        ok = self.sync_manager.export_passwords(active, path)
                        if ok:
                            self.status_label.setText(f"Passwords exported to {path}")
                        else:
                            self.status_label.setText(
                                "Passwords not exported \u2014 vault is locked. "
                                "Open Password Manager and unlock it first."
                            )
                    elif etype == "passwords_csv":
                        ok = self.sync_manager.export_passwords_csv(active, path)
                        if ok:
                            self.status_label.setText(f"Passwords exported to {path}")
                        else:
                            self.status_label.setText(
                                "Passwords not exported \u2014 vault is locked. "
                                "Open Password Manager and unlock it first."
                            )

    def bookmark_page(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view:
                page = tab.web_view.page()
                url = page.url().toString() if page.url() else ""
                title = page.title() if page.title() else url
                active = self.sync_manager.active_profile_name
                if active:
                    self.sync_manager.add_bookmark(active, url, title)
                    self.status_label.setText(f"Bookmarked: {title}")

    def show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                padding: 2px 0px;
                font-size: {FONTS['size_sm']}px;
            }}
            QMenu::item {{
                padding: 5px 20px;
            }}
            QMenu::item:selected {{
                background: {COLORS['accent_darker']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {COLORS['border']};
                margin: 2px 0px;
            }}
        """)

        menu.addAction("New Tab (Ctrl+T)", self.add_new_tab_shortcut)
        menu.addAction("Close Tab (Ctrl+W)", self.close_current_tab)
        menu.addSeparator()
        menu.addAction("Reload (F5)", self.reload_page)
        menu.addAction("Back (Alt+Left)", self.navigate_back)
        menu.addAction("Forward (Alt+Right)", self.navigate_forward)
        menu.addSeparator()
        menu.addAction("Find in Page (Ctrl+F)", self.find_in_page)
        menu.addAction("Show Headers (Ctrl+Shift+H)", self.show_headers)
        menu.addAction("Toggle Terminal (Ctrl+`)", self.toggle_terminal)
        menu.addSeparator()
        menu.addAction("Bookmark (Ctrl+D)", self.bookmark_page)
        menu.addAction("View Bookmarks", self._show_bookmarks)
        menu.addSeparator()
        menu.addAction("Import Browser Data...", self.open_import_dialog)
        menu.addAction("Password Manager...", self.open_password_manager)
        menu.addSeparator()
        menu.addAction(
            f"Reef Shield: {'ON' if self.reef_shield.enabled else 'OFF'}",
            self.toggle_reef_shield
        )
        menu.addAction("Clear Data (Ctrl+Shift+Del)", self.clear_data)
        menu.addSeparator()
        menu.addAction("Settings", self.open_settings)
        menu.addAction("Profiles", self.open_profile_manager)

        menu.exec(self.btn_menu.mapToGlobal(self.btn_menu.rect().bottomLeft()))

    def _show_bookmarks(self):
        active = self.sync_manager.active_profile_name
        if not active:
            self.status_label.setText("No active profile for bookmarks")
            return
        bookmarks = self.sync_manager.get_bookmarks(active)
        if not bookmarks:
            self.status_label.setText("No bookmarks in current profile")
            return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                padding: 2px 0px;
                font-size: {FONTS['size_sm']}px;
            }}
            QMenu::item {{
                padding: 5px 20px;
            }}
            QMenu::item:selected {{
                background: {COLORS['accent_darker']};
            }}
        """)
        for bm in bookmarks[-30:]:
            title = bm.get("title", bm.get("url", ""))[:60]
            url = bm.get("url", "")
            menu.addAction(title, lambda u=url: self._open_bookmark(u))
        menu.exec(self.btn_bookmark.mapToGlobal(
            self.btn_bookmark.rect().bottomLeft()
        ))

    def _open_bookmark(self, url):
        idx = self.tab_bar.currentIndex()
        if idx >= 0 and idx < len(self.tabs):
            tab = self.tabs[idx]
            if tab.web_view:
                tab.web_view.setUrl(QUrl(url))

    def clear_data(self):
        profile_name = self.sync_manager.active_profile_name
        if not profile_name:
            self.web_profile.cookieStore().deleteAllCookies()
            self.status_label.setText("Browsing data cleared")
            return

        from PySide6.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QVBoxLayout,
        )
        dlg = QDialog(self)
        dlg.setWindowTitle("Clear Browsing Data")
        dlg.setMinimumSize(350, 200)
        dlg.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        dlg_layout = QVBoxLayout(dlg)
        lbl = QLabel("Select data to clear:")
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 4px;")
        dlg_layout.addWidget(lbl)

        cookies_cb = QCheckBox("Cookies")
        cookies_cb.setChecked(True)
        cookies_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_primary']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {COLORS['border']};
                background: {COLORS['bg_input']};
            }}
            QCheckBox::indicator:checked {{
                background: {COLORS['accent']};
                border-color: {COLORS['accent']};
            }}
        """)
        dlg_layout.addWidget(cookies_cb)

        cache_cb = QCheckBox("Cache")
        cache_cb.setChecked(True)
        cache_cb.setStyleSheet(cookies_cb.styleSheet())
        dlg_layout.addWidget(cache_cb)

        history_cb = QCheckBox("History")
        history_cb.setChecked(True)
        history_cb.setStyleSheet(cookies_cb.styleSheet())
        dlg_layout.addWidget(history_cb)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_elevated']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                padding: 6px 16px;
            }}
        """)
        cancel.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel)
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_darker']};
                color: {COLORS['bg_primary']};
                border: none;
                padding: 6px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['accent']};
            }}
        """)
        clear_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(clear_btn)
        dlg_layout.addLayout(btn_row)

        if dlg.exec() == QDialog.Accepted:
            result = self.sync_manager.clear_browsing_data(
                profile_name,
                clear_cookies=cookies_cb.isChecked(),
                clear_cache=cache_cb.isChecked(),
                clear_history=history_cb.isChecked()
            )
            if cookies_cb.isChecked():
                self.web_profile.cookieStore().deleteAllCookies()
            parts = []
            if result.get("cookies"):
                parts.append("cookies")
            if result.get("cache"):
                parts.append("cache")
            if result.get("history"):
                parts.append(f"{result['history']} history entries")
            self.status_label.setText(
                f"Cleared: {', '.join(parts)}" if parts else "Data cleared"
            )

    def open_import_dialog(self):
        dialog = ImportDialog(self.sync_manager, self)
        dialog.exec()

    def open_password_manager(self):
        dialog = PasswordManagerDialog(self.sync_manager, self)
        dialog.exec()

    def on_page_load_started(self, tab):
        if tab.web_view:
            idx = self.tab_bar.indexOf(tab.web_view)
            if idx >= 0:
                self.tab_bar.setTabText(idx, "Loading...")
        self.load_progress.show()

    def on_page_load_progress(self, progress):
        self.load_progress.setValue(progress)

    def on_page_load_finished(self, tab, ok):
        self.load_progress.hide()
        if tab.web_view:
            idx = self.tab_bar.indexOf(tab.web_view)
            if idx >= 0:
                title = tab.web_view.page().title() or tab.url
                short_title = title[:40] + "..." if len(title) > 40 else title
                self.tab_bar.setTabText(idx, short_title)
            if ok:
                page = tab.web_view.page()
                if page and page.url():
                    current_url = page.url().toString()
                    tab.url = current_url
                    self.url_bar.setText(current_url)
                    active = self.sync_manager.active_profile_name
                    if active:
                        self.sync_manager.add_history(
                            active, current_url,
                            page.title() or current_url
                        )
                self._inject_css_filter(tab)
            else:
                self.status_label.setText("Failed to load page")

    def on_title_changed(self, tab, title):
        if tab.web_view:
            idx = self.tab_bar.indexOf(tab.web_view)
            if idx >= 0:
                short_title = title[:40] + "..." if len(title) > 40 else title
                self.tab_bar.setTabText(idx, short_title)

    def on_url_changed(self, tab, url):
        if tab.web_view:
            idx = self.tab_bar.indexOf(tab.web_view)
            if idx >= 0 and idx == self.tab_bar.currentIndex():
                self.url_bar.setText(url.toString())
                tab.url = url.toString()

    def _inject_css_filter(self, tab):
        if not tab.web_view:
            return
        css = self.reef_shield.get_injection_css()
        js = f"""
        (function() {{
            var style = document.createElement('style');
            style.textContent = `{css}`;
            document.head.appendChild(style);
        }})();
        """
        page = tab.web_view.page()
        page.runJavaScript(js)

    def closeEvent(self, event):
        if hasattr(self, '_devtools_view') and self._devtools_view:
            self._devtools_view.close()
        for tab in self.tabs:
            if tab.web_view:
                tab.web_view.deleteLater()
        event.accept()
