"""
Surfline Browser - Settings, Import & Password Manager Dialogs
"""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.Surfline.src.importer import BrowserImporter
from apps.Surfline.src.theme import COLORS, FONTS

SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={}",
    "DuckDuckGo": "https://duckduckgo.com/?q={}",
    "Bing": "https://www.bing.com/search?q={}",
    "Brave Search": "https://search.brave.com/search?q={}",
    "Startpage": "https://www.startpage.com/do/search?q={}",
    "Mojeek": "https://www.mojeek.com/search?q={}",
    "Yahoo": "https://search.yahoo.com/search?p={}",
}

GROUP_BOX_STYLE = f"""
    QGroupBox {{
        color: {COLORS['accent']};
        border: 1px solid {COLORS['border']};
        margin-top: 8px;
        padding-top: 16px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
    }}
"""

CHECKBOX_STYLE = f"""
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
"""

LABEL_STYLE = f"color: {COLORS['text_secondary']};"

INPUT_STYLE = f"""
    QLineEdit {{
        background: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 4px 8px;
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
    }}
    QLineEdit:focus {{
        border: 1px solid {COLORS['accent']};
    }}
"""

SPINBOX_STYLE = f"""
    QSpinBox {{
        background: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 4px 8px;
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
    }}
    QSpinBox:focus {{
        border: 1px solid {COLORS['accent']};
    }}
"""

COMBO_STYLE = f"""
    QComboBox {{
        background: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 4px 8px;
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
    }}
    QComboBox:focus {{
        border: 1px solid {COLORS['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 16px;
    }}
    QComboBox QAbstractItemView {{
        background: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        selection-background-color: {COLORS['accent_darker']};
    }}
"""

BTN_STYLE = f"""
    QPushButton {{
        background: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 6px 16px;
        min-width: 60px;
    }}
    QPushButton:hover {{
        border-color: {COLORS['accent']};
    }}
"""

HEADER_STYLE = f"""
    QLabel {{
        color: {COLORS['accent']};
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_lg']}px;
        font-weight: bold;
        letter-spacing: 2px;
        padding: 8px 0;
        border-bottom: 1px solid {COLORS['border']};
    }}
"""

DIALOG_STYLE = f"""
    QDialog {{
        background: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
    }}
"""

TABLE_STYLE = f"""
    QTableWidget {{
        background: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        gridline-color: {COLORS['border']};
        font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
        font-size: {FONTS['size_sm']}px;
    }}
    QTableWidget::item {{
        padding: 4px 8px;
    }}
    QTableWidget::item:selected {{
        background: {COLORS['accent_darker']};
        color: {COLORS['text_primary']};
    }}
    QHeaderView::section {{
        background: {COLORS['bg_secondary']};
        color: {COLORS['accent']};
        border: none;
        border-bottom: 1px solid {COLORS['border']};
        padding: 4px 8px;
        font-weight: bold;
        letter-spacing: 1px;
    }}
"""


def _make_header(text):
    header = QLabel(text)
    header.setStyleSheet(HEADER_STYLE)
    return header


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = dict(settings)
        self.result_settings = dict(settings)
        self.setWindowTitle("Surfline Settings")
        self.setMinimumSize(580, 520)
        self.setStyleSheet(DIALOG_STYLE)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(_make_header("SURFLINE SETTINGS"))

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['bg_primary']};
            }}
            QTabBar::tab {{
                background: {COLORS['tab_inactive']};
                color: {COLORS['text_secondary']};
                padding: 4px 14px;
                border: none;
                border-bottom: 2px solid transparent;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['tab_active']};
                color: {COLORS['accent']};
                border-bottom: 2px solid {COLORS['accent']};
            }}
        """)

        tabs.addTab(self._general_tab(), "GENERAL")
        tabs.addTab(self._appearance_tab(), "APPEARANCE")
        tabs.addTab(self._privacy_tab(), "PRIVACY")
        tabs.addTab(self._search_tab(), "SEARCH")
        tabs.addTab(self._advanced_tab(), "ADVANCED")
        tabs.addTab(self._data_tab(), "DATA")

        layout.addWidget(tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BTN_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
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
        save_btn.clicked.connect(self.save_settings)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _general_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignTop)

        g1 = QGroupBox("Homepage & Startup")
        g1.setStyleSheet(GROUP_BOX_STYLE)
        g1_lay = QVBoxLayout()

        row = QHBoxLayout()
        row.addWidget(QLabel("Homepage URL:"))
        row.addWidget(QLabel(LABEL_STYLE))
        self.homepage_edit = QLineEdit(self.settings.get("homepage", "about:blank"))
        self.homepage_edit.setStyleSheet(INPUT_STYLE)
        self.homepage_edit.setPlaceholderText("about:blank or https://...")
        row.addWidget(self.homepage_edit)
        g1_lay.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Startup Page:"))
        row2.addWidget(QLabel(LABEL_STYLE))
        self.startup_combo = QComboBox()
        self.startup_combo.setStyleSheet(COMBO_STYLE)
        self.startup_combo.addItems(["New Tab", "Homepage", "Last Session"])
        startup_val = self.settings.get("startup_page", "new_tab")
        idx = {"new_tab": 0, "homepage": 1, "last_session": 2}.get(startup_val, 0)
        self.startup_combo.setCurrentIndex(idx)
        row2.addWidget(self.startup_combo)
        g1_lay.addLayout(row2)

        g1.setLayout(g1_lay)
        lay.addWidget(g1)

        g2 = QGroupBox("Browser Behavior")
        g2.setStyleSheet(GROUP_BOX_STYLE)
        g2_lay = QVBoxLayout()

        self.javascript_check = QCheckBox("Enable JavaScript")
        self.javascript_check.setChecked(self.settings.get("javascript_enabled", True))
        self.javascript_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.javascript_check)

        self.images_check = QCheckBox("Load Images")
        self.images_check.setChecked(self.settings.get("images_enabled", True))
        self.images_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.images_check)

        self.webgl_check = QCheckBox("Enable WebGL")
        self.webgl_check.setChecked(self.settings.get("enable_webgl", True))
        self.webgl_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.webgl_check)

        self.webaudio_check = QCheckBox("Enable WebAudio")
        self.webaudio_check.setChecked(self.settings.get("enable_webaudio", True))
        self.webaudio_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.webaudio_check)

        self.notifications_check = QCheckBox("Allow Notifications")
        self.notifications_check.setChecked(self.settings.get("enable_notifications", True))
        self.notifications_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.notifications_check)

        self.geolocation_check = QCheckBox("Allow Geolocation")
        self.geolocation_check.setChecked(self.settings.get("enable_geolocation", False))
        self.geolocation_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.geolocation_check)

        self.autoplay_check = QCheckBox("Auto-play Media")
        self.autoplay_check.setChecked(self.settings.get("auto_play_media", True))
        self.autoplay_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.autoplay_check)

        g2.setLayout(g2_lay)
        lay.addWidget(g2)

        g3 = QGroupBox("Downloads")
        g3.setStyleSheet(GROUP_BOX_STYLE)
        g3_lay = QHBoxLayout()
        g3_lay.addWidget(QLabel("Download Path:"))
        self.download_path_edit = QLineEdit(self.settings.get("download_path", ""))
        self.download_path_edit.setStyleSheet(INPUT_STYLE)
        self.download_path_edit.setPlaceholderText("(system default)")
        g3_lay.addWidget(self.download_path_edit, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet(BTN_STYLE)
        browse_btn.clicked.connect(self._browse_download_path)
        g3_lay.addWidget(browse_btn)
        self.ask_download_check = QCheckBox("Ask where to save")
        self.ask_download_check.setChecked(self.settings.get("ask_download_location", True))
        self.ask_download_check.setStyleSheet(CHECKBOX_STYLE)
        g3_lay.addWidget(self.ask_download_check)
        g3.setLayout(g3_lay)
        lay.addWidget(g3)

        lay.addStretch()
        return w

    def _appearance_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignTop)

        g1 = QGroupBox("Interface")
        g1.setStyleSheet(GROUP_BOX_STYLE)
        g1_lay = QVBoxLayout()

        row = QHBoxLayout()
        row.addWidget(QLabel("Default Font Size:"))
        row.addWidget(QLabel(LABEL_STYLE))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setStyleSheet(SPINBOX_STYLE)
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings.get("font_size", 12))
        self.font_size_spin.setSuffix(" px")
        row.addWidget(self.font_size_spin)
        row.addStretch()
        g1_lay.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Page Zoom:"))
        row2.addWidget(QLabel(LABEL_STYLE))
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setStyleSheet(SPINBOX_STYLE)
        self.zoom_spin.setRange(50, 200)
        self.zoom_spin.setValue(self.settings.get("default_zoom", 100))
        self.zoom_spin.setSuffix("%")
        self.zoom_spin.setSingleStep(10)
        row2.addWidget(self.zoom_spin)
        row2.addStretch()
        g1_lay.addLayout(row2)

        self.smooth_scroll_check = QCheckBox("Smooth Scrolling")
        self.smooth_scroll_check.setChecked(self.settings.get("smooth_scrolling", True))
        self.smooth_scroll_check.setStyleSheet(CHECKBOX_STYLE)
        g1_lay.addWidget(self.smooth_scroll_check)

        self.show_bookmarks_bar_check = QCheckBox("Show Bookmarks Bar")
        self.show_bookmarks_bar_check.setChecked(self.settings.get("show_bookmarks_bar", False))
        self.show_bookmarks_bar_check.setStyleSheet(CHECKBOX_STYLE)
        g1_lay.addWidget(self.show_bookmarks_bar_check)

        g1.setLayout(g1_lay)
        lay.addWidget(g1)

        g2 = QGroupBox("Tab Behavior")
        g2.setStyleSheet(GROUP_BOX_STYLE)
        g2_lay = QVBoxLayout()

        self.tab_close_check = QCheckBox("Close tab activates nearest tab")
        self.tab_close_check.setChecked(self.settings.get("tab_close_activates_nearest", True))
        self.tab_close_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.tab_close_check)

        self.warn_close_check = QCheckBox("Warn when closing multiple tabs")
        self.warn_close_check.setChecked(self.settings.get("warn_on_close", False))
        self.warn_close_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.warn_close_check)

        g2.setLayout(g2_lay)
        lay.addWidget(g2)

        g3 = QGroupBox("Theme Accent Color")
        g3.setStyleSheet(GROUP_BOX_STYLE)
        g3_lay = QHBoxLayout()

        self.accent_colors = {
            "Teal (#00F2C2)": COLORS["seafoam"],
            "Blue (#4A9EFF)": "#4A9EFF",
            "Purple (#B24BF3)": "#B24BF3",
            "Orange (#FF8C42)": "#FF8C42",
            "Red (#FF4757)": "#FF4757",
            "Green (#2ED573)": "#2ED573",
            "Yellow (#FFC312)": "#FFC312",
            "White (#FFFFFF)": "#FFFFFF",
        }
        self.accent_combo = QComboBox()
        self.accent_combo.setStyleSheet(COMBO_STYLE)
        for label in self.accent_colors:
            self.accent_combo.addItem(label)
        current_accent = self.settings.get("accent_color", COLORS["seafoam"])
        for i, (label, color) in enumerate(self.accent_colors.items()):
            if color == current_accent:
                self.accent_combo.setCurrentIndex(i)
                break
        g3_lay.addWidget(self.accent_combo)
        g3_lay.addStretch()
        g3.setLayout(g3_lay)
        lay.addWidget(g3)

        lay.addStretch()
        return w

    def _privacy_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignTop)

        g1 = QGroupBox("Tracking & Cookies")
        g1.setStyleSheet(GROUP_BOX_STYLE)
        g1_lay = QVBoxLayout()

        self.dnt_check = QCheckBox("Send Do Not Track header")
        self.dnt_check.setChecked(self.settings.get("enable_do_not_track", True))
        self.dnt_check.setStyleSheet(CHECKBOX_STYLE)
        g1_lay.addWidget(self.dnt_check)

        self.cookies_check = QCheckBox("Accept Cookies")
        self.cookies_check.setChecked(self.settings.get("accept_cookies", True))
        self.cookies_check.setStyleSheet(CHECKBOX_STYLE)
        g1_lay.addWidget(self.cookies_check)

        g1.setLayout(g1_lay)
        lay.addWidget(g1)

        g2 = QGroupBox("Clear Data on Exit")
        g2.setStyleSheet(GROUP_BOX_STYLE)
        g2_lay = QVBoxLayout()

        self.clear_on_exit_check = QCheckBox("Clear data when browser closes")
        self.clear_on_exit_check.setChecked(self.settings.get("clear_on_exit", False))
        self.clear_on_exit_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.clear_on_exit_check)

        self.clear_cookies_check = QCheckBox("Clear Cookies")
        self.clear_cookies_check.setChecked(self.settings.get("clear_cookies", False))
        self.clear_cookies_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.clear_cookies_check)

        self.clear_cache_check = QCheckBox("Clear Cache")
        self.clear_cache_check.setChecked(self.settings.get("clear_cache", False))
        self.clear_cache_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.clear_cache_check)

        self.clear_history_check = QCheckBox("Clear History")
        self.clear_history_check.setChecked(self.settings.get("clear_history", False))
        self.clear_history_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.clear_history_check)

        g2.setLayout(g2_lay)
        lay.addWidget(g2)

        lay.addStretch()
        return w

    def _search_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignTop)

        g1 = QGroupBox("Default Search Engine")
        g1.setStyleSheet(GROUP_BOX_STYLE)
        g1_lay = QVBoxLayout()

        row = QHBoxLayout()
        row.addWidget(QLabel("Search Engine:"))
        row.addWidget(QLabel(LABEL_STYLE))
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.setStyleSheet(COMBO_STYLE)
        for name in SEARCH_ENGINES:
            self.search_engine_combo.addItem(name)
        current_engine = self.settings.get("search_engine", "Google")
        idx = list(SEARCH_ENGINES.keys()).index(current_engine) if current_engine in SEARCH_ENGINES else 0
        self.search_engine_combo.setCurrentIndex(idx)
        self.search_engine_combo.currentTextChanged.connect(self._on_search_engine_changed)
        row.addWidget(self.search_engine_combo)
        row.addStretch()
        g1_lay.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Custom URL:"))
        row2.addWidget(QLabel(LABEL_STYLE))
        self.search_url_edit = QLineEdit(self.settings.get("search_url", SEARCH_ENGINES["Google"]))
        self.search_url_edit.setStyleSheet(INPUT_STYLE)
        self.search_url_edit.setPlaceholderText("https://example.com/search?q={}")
        row2.addWidget(self.search_url_edit, 1)
        g1_lay.addLayout(row2)

        note = QLabel("Use {} as placeholder for search query")
        note.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_xs']}px; font-style: italic;")
        g1_lay.addWidget(note)

        g1.setLayout(g1_lay)
        lay.addWidget(g1)

        lay.addStretch()
        return w

    def _advanced_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignTop)

        g1 = QGroupBox("WebEngine Features")
        g1.setStyleSheet(GROUP_BOX_STYLE)
        g1_lay = QVBoxLayout()

        self.debug_check = QCheckBox("Enable DevTools (F12)")
        self.debug_check.setChecked(self.settings.get("enable_devtools", True))
        self.debug_check.setStyleSheet(CHECKBOX_STYLE)
        g1_lay.addWidget(self.debug_check)

        g1.setLayout(g1_lay)
        lay.addWidget(g1)

        g2 = QGroupBox("Profile & Data")
        g2.setStyleSheet(GROUP_BOX_STYLE)
        g2_lay = QVBoxLayout()

        self.show_statusbar_check = QCheckBox("Show Status Bar")
        self.show_statusbar_check.setChecked(self.settings.get("show_statusbar", True))
        self.show_statusbar_check.setStyleSheet(CHECKBOX_STYLE)
        g2_lay.addWidget(self.show_statusbar_check)

        g2.setLayout(g2_lay)
        lay.addWidget(g2)

        g3 = QGroupBox("Keyboard Shortcuts Reference")
        g3.setStyleSheet(GROUP_BOX_STYLE)
        g3_lay = QVBoxLayout()

        shortcuts_text = QTextEdit()
        shortcuts_text.setReadOnly(True)
        shortcuts_text.setMaximumHeight(200)
        shortcuts_text.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['terminal_bg']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 6px;
            }}
        """)
        shortcuts_text.setPlainText(
            "Ctrl+T          New Tab\n"
            "Ctrl+W          Close Tab\n"
            "Ctrl+Tab        Next Tab\n"
            "Ctrl+Shift+Tab  Previous Tab\n"
            "F5 / Ctrl+R     Reload Page\n"
            "Alt+Left/Right  Back / Forward\n"
            "Alt+Home        Go Home\n"
            "Ctrl+L / F6     Focus URL Bar\n"
            "Ctrl+F          Find in Page\n"
            "F12             Toggle DevTools\n"
            "Ctrl+`          Toggle Terminal\n"
            "Ctrl+D          Bookmark Page\n"
            "Ctrl+Shift+Del  Clear Data\n"
            "Ctrl+1-9        Switch to Tab N\n"
            "Escape          Stop Loading"
        )
        g3_lay.addWidget(shortcuts_text)
        g3.setLayout(g3_lay)
        lay.addWidget(g3)

        lay.addStretch()
        return w

    def _data_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignTop)

        g1 = QGroupBox("Export")
        g1.setStyleSheet(GROUP_BOX_STYLE)
        g1_lay = QVBoxLayout()

        btn_row = QHBoxLayout()
        export_bm_btn = QPushButton("Export Bookmarks (JSON)")
        export_bm_btn.setStyleSheet(BTN_STYLE)
        export_bm_btn.clicked.connect(self._export_bookmarks)
        btn_row.addWidget(export_bm_btn)

        export_pw_btn = QPushButton("Export Passwords (JSON)")
        export_pw_btn.setStyleSheet(BTN_STYLE)
        export_pw_btn.clicked.connect(self._export_passwords)
        btn_row.addWidget(export_pw_btn)

        export_csv_btn = QPushButton("Export Passwords (CSV)")
        export_csv_btn.setStyleSheet(BTN_STYLE)
        export_csv_btn.clicked.connect(self._export_passwords_csv)
        btn_row.addWidget(export_csv_btn)

        btn_row.addStretch()
        g1_lay.addLayout(btn_row)

        g1.setLayout(g1_lay)
        lay.addWidget(g1)

        lay.addStretch()
        return w

    def _on_search_engine_changed(self, name):
        if name in SEARCH_ENGINES:
            self.search_url_edit.setText(SEARCH_ENGINES[name])

    def _browse_download_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if path:
            self.download_path_edit.setText(path)

    def _export_bookmarks(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Bookmarks", "bookmarks.json", "JSON Files (*.json)"
        )
        if path:
            self._pending_export = ("bookmarks", path)
            self.accept()

    def _export_passwords(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Passwords", "passwords.json", "JSON Files (*.json)"
        )
        if path:
            self._pending_export = ("passwords_json", path)
            self.accept()

    def _export_passwords_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Passwords", "passwords.csv", "CSV Files (*.csv)"
        )
        if path:
            self._pending_export = ("passwords_csv", path)
            self.accept()

    def save_settings(self):
        startup_map = {0: "new_tab", 1: "homepage", 2: "last_session"}
        engine_name = self.search_engine_combo.currentText()

        self.result_settings.update({
            "homepage": self.homepage_edit.text(),
            "startup_page": startup_map.get(self.startup_combo.currentIndex(), "new_tab"),
            "javascript_enabled": self.javascript_check.isChecked(),
            "images_enabled": self.images_check.isChecked(),
            "enable_webgl": self.webgl_check.isChecked(),
            "enable_webaudio": self.webaudio_check.isChecked(),
            "enable_notifications": self.notifications_check.isChecked(),
            "enable_geolocation": self.geolocation_check.isChecked(),
            "auto_play_media": self.autoplay_check.isChecked(),
            "download_path": self.download_path_edit.text(),
            "ask_download_location": self.ask_download_check.isChecked(),
            "font_size": self.font_size_spin.value(),
            "default_zoom": self.zoom_spin.value(),
            "smooth_scrolling": self.smooth_scroll_check.isChecked(),
            "show_bookmarks_bar": self.show_bookmarks_bar_check.isChecked(),
            "tab_close_activates_nearest": self.tab_close_check.isChecked(),
            "warn_on_close": self.warn_close_check.isChecked(),
            "accent_color": self.accent_colors.get(
                self.accent_combo.currentText(), "#00F2C2"
            ),
            "enable_do_not_track": self.dnt_check.isChecked(),
            "accept_cookies": self.cookies_check.isChecked(),
            "clear_on_exit": self.clear_on_exit_check.isChecked(),
            "clear_cookies": self.clear_cookies_check.isChecked(),
            "clear_cache": self.clear_cache_check.isChecked(),
            "clear_history": self.clear_history_check.isChecked(),
            "search_engine": engine_name,
            "search_url": self.search_url_edit.text(),
            "enable_devtools": self.debug_check.isChecked(),
            "show_statusbar": self.show_statusbar_check.isChecked(),
        })
        self.accept()


class ImportDialog(QDialog):
    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self.importer = BrowserImporter()
        self.setWindowTitle("Import Browser Data")
        self.setMinimumSize(620, 500)
        self.setStyleSheet(DIALOG_STYLE)
        self.scan_results = []
        self.setup_ui()
        self._scan_browsers()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(_make_header("IMPORT BROWSER DATA"))

        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Import to Profile:"))
        source_row.addWidget(QLabel(LABEL_STYLE))
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(COMBO_STYLE)
        for name in self.sync_manager.get_profile_names():
            self.profile_combo.addItem(name)
        active = self.sync_manager.active_profile_name
        if active:
            idx = self.sync_manager.get_profile_names().index(active) if active in self.sync_manager.get_profile_names() else 0
            self.profile_combo.setCurrentIndex(idx)
        source_row.addWidget(self.profile_combo)
        source_row.addStretch()
        layout.addLayout(source_row)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['bg_primary']};
            }}
            QTabBar::tab {{
                background: {COLORS['tab_inactive']};
                color: {COLORS['text_secondary']};
                padding: 4px 14px;
                border: none;
                border-bottom: 2px solid transparent;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['tab_active']};
                color: {COLORS['accent']};
                border-bottom: 2px solid {COLORS['accent']};
            }}
        """)

        tabs.addTab(self._browsers_tab(), "DETECTED BROWSERS")
        tabs.addTab(self._file_tab(), "IMPORT FROM FILE")
        layout.addWidget(tabs)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
            font-size: {FONTS['size_sm']}px;
            padding: 4px;
        """)
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(BTN_STYLE)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _browsers_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        self.browser_table = QTableWidget()
        self.browser_table.setStyleSheet(TABLE_STYLE)
        self.browser_table.setColumnCount(6)
        self.browser_table.setHorizontalHeaderLabels([
            "Browser", "Status", "Bookmarks", "History", "Passwords", "Settings"
        ])
        self.browser_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.browser_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.browser_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.browser_table.verticalHeader().setVisible(False)
        lay.addWidget(self.browser_table)

        import_row = QHBoxLayout()
        self.import_bookmarks_check = QCheckBox("Bookmarks")
        self.import_bookmarks_check.setChecked(True)
        self.import_bookmarks_check.setStyleSheet(CHECKBOX_STYLE)
        import_row.addWidget(self.import_bookmarks_check)

        self.import_history_check = QCheckBox("History")
        self.import_history_check.setChecked(True)
        self.import_history_check.setStyleSheet(CHECKBOX_STYLE)
        import_row.addWidget(self.import_history_check)

        self.import_passwords_check = QCheckBox("Passwords")
        self.import_passwords_check.setChecked(True)
        self.import_passwords_check.setStyleSheet(CHECKBOX_STYLE)
        import_row.addWidget(self.import_passwords_check)

        self.import_settings_check = QCheckBox("Settings")
        self.import_settings_check.setChecked(True)
        self.import_settings_check.setStyleSheet(CHECKBOX_STYLE)
        import_row.addWidget(self.import_settings_check)

        import_row.addStretch()

        scan_btn = QPushButton("Rescan")
        scan_btn.setStyleSheet(BTN_STYLE)
        scan_btn.clicked.connect(self._scan_browsers)
        import_row.addWidget(scan_btn)

        import_btn = QPushButton("Import Selected")
        import_btn.setStyleSheet(f"""
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
        import_btn.clicked.connect(self._import_from_browser)
        import_row.addWidget(import_btn)

        lay.addLayout(import_row)
        return w

    def _file_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        info = QLabel(
            "Import bookmarks or passwords from a file.\n"
            "Supported formats: CSV, JSON (password export format), HTML (bookmark export)"
        )
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 8px;")
        info.setWordWrap(True)
        lay.addWidget(info)

        file_row = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setStyleSheet(INPUT_STYLE)
        self.file_path_edit.setPlaceholderText("Select a file to import...")
        file_row.addWidget(self.file_path_edit, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet(BTN_STYLE)
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        lay.addLayout(file_row)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Data Type:"))
        type_row.addWidget(QLabel(LABEL_STYLE))
        self.file_type_combo = QComboBox()
        self.file_type_combo.setStyleSheet(COMBO_STYLE)
        self.file_type_combo.addItems(["Auto-detect", "Bookmarks", "Passwords"])
        type_row.addWidget(self.file_type_combo)
        type_row.addStretch()
        lay.addLayout(type_row)

        self.file_preview = QTextEdit()
        self.file_preview.setReadOnly(True)
        self.file_preview.setMaximumHeight(120)
        self.file_preview.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['terminal_bg']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 6px;
            }}
        """)
        self.file_preview.setPlainText("No file selected.")
        lay.addWidget(self.file_preview)

        import_file_btn = QPushButton("Import from File")
        import_file_btn.setStyleSheet(f"""
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
        import_file_btn.clicked.connect(self._import_from_file)
        lay.addWidget(import_file_btn)

        lay.addStretch()
        return w

    def _scan_browsers(self):
        self.scan_results = []
        browsers = self.importer.get_available_browsers()
        for b in browsers:
            self.importer.scan_browser(b)
            self.scan_results.append(b)

        self.browser_table.setRowCount(len(self.scan_results))
        for i, b in enumerate(self.scan_results):
            status = "Available" if b.available else "Not Found"
            status_color = COLORS['accent'] if b.available else COLORS['error']
            items = [b.name, status, str(b.bookmarks_found), str(b.history_found), str(b.passwords_found), str(b.settings_found)]
            for j, text in enumerate(items):
                item = QTableWidgetItem(text)
                if j == 1:
                    item.setForeground(QColor(status_color))
                self.browser_table.setItem(i, j, item)

        if not self.scan_results:
            self.browser_table.setRowCount(1)
            item = QTableWidgetItem("No browsers detected")
            item.setTextAlignment(Qt.AlignCenter)
            self.browser_table.setItem(0, 0, item)
            self.browser_table.setSpan(0, 0, 1, 6)

    def _import_from_browser(self):
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return

        selected_rows = set(idx.row() for idx in self.browser_table.selectedIndexes())
        if not selected_rows:
            self.status_label.setText("Select a browser from the table first")
            return

        total_bm = 0
        total_hist = 0
        total_pw = 0
        total_settings = 0

        for row in selected_rows:
            if row >= len(self.scan_results):
                continue
            browser = self.scan_results[row]
            if not browser.available:
                continue

            if self.import_bookmarks_check.isChecked():
                if browser.browser_type == "chromium":
                    profiles = self.importer._get_chromium_profiles(browser.profile_path)
                    for prof_dir in profiles:
                        bm = self.importer.import_bookmarks_chromium(prof_dir)
                        total_bm += self.sync_manager.import_bookmarks(profile_name, bm)
                elif browser.browser_type == "firefox":
                    profiles = self.importer._get_firefox_profiles(browser.profile_path)
                    for prof_dir in profiles:
                        bm = self.importer.import_bookmarks_firefox(prof_dir)
                        total_bm += self.sync_manager.import_bookmarks(profile_name, bm)

            if self.import_history_check.isChecked():
                if browser.browser_type == "chromium":
                    profiles = self.importer._get_chromium_profiles(browser.profile_path)
                    for prof_dir in profiles:
                        hist = self.importer.import_history_chromium(prof_dir)
                        total_hist += self.sync_manager.import_history(profile_name, hist)
                elif browser.browser_type == "firefox":
                    profiles = self.importer._get_firefox_profiles(browser.profile_path)
                    for prof_dir in profiles:
                        hist = self.importer.import_history_firefox(prof_dir)
                        total_hist += self.sync_manager.import_history(profile_name, hist)

            if self.import_passwords_check.isChecked():
                if browser.browser_type == "chromium":
                    profiles = self.importer._get_chromium_profiles(browser.profile_path)
                    for prof_dir in profiles:
                        pw = self.importer.import_passwords_chromium(prof_dir)
                        total_pw += self.sync_manager.import_passwords(profile_name, pw)
                elif browser.browser_type == "firefox":
                    profiles = self.importer._get_firefox_profiles(browser.profile_path)
                    for prof_dir in profiles:
                        pw = self.importer.import_passwords_firefox(prof_dir)
                        total_pw += self.sync_manager.import_passwords(profile_name, pw)

            if self.import_settings_check.isChecked():
                if browser.browser_type == "chromium":
                    profiles = self.importer._get_chromium_profiles(browser.profile_path)
                    for prof_dir in profiles:
                        settings = self.importer.import_settings_chromium(prof_dir)
                        if settings:
                            total_settings += self.sync_manager.import_settings(settings)
                elif browser.browser_type == "firefox":
                    profiles = self.importer._get_firefox_profiles(browser.profile_path)
                    for prof_dir in profiles:
                        settings = self.importer.import_settings_firefox(prof_dir)
                        if settings:
                            total_settings += self.sync_manager.import_settings(settings)

        parts = []
        if total_bm:
            parts.append(f"{total_bm} bookmarks")
        if total_hist:
            parts.append(f"{total_hist} history entries")
        if total_pw:
            parts.append(f"{total_pw} passwords")
        if total_settings:
            parts.append(f"{total_settings} settings")
        if parts:
            self.status_label.setText(f"Imported: {', '.join(parts)}")
            self.status_label.setStyleSheet(f"""
                color: {COLORS['accent']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 4px;
            """)
        else:
            self.status_label.setText("No new data imported (duplicates skipped or no data found)")
            self.status_label.setStyleSheet(f"""
                color: {COLORS['warning']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 4px;
            """)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import File", "",
            "All Supported (*.csv *.json *.html);;CSV Files (*.csv);;JSON Files (*.json);;HTML Bookmarks (*.html)"
        )
        if path:
            self.file_path_edit.setText(path)
            self._preview_file(path)

    def _preview_file(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read(2000)
            self.file_preview.setPlainText(content)
        except Exception as e:
            self.file_preview.setPlainText(f"Error reading file: {e}")

    def _import_from_file(self):
        path = self.file_path_edit.text().strip()
        if not path or not os.path.exists(path):
            self.status_label.setText("Select a valid file first")
            return

        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return

        data, source = self.importer.import_from_file(path)
        if not data:
            self.status_label.setText("No data found in file or unsupported format")
            self.status_label.setStyleSheet(f"""
                color: {COLORS['error']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 4px;
            """)
            return

        type_choice = self.file_type_combo.currentText()
        is_password = (
            type_choice == "Passwords" or
            (type_choice == "Auto-detect" and any(d.get("password") for d in data))
        )

        if is_password:
            count = self.sync_manager.import_passwords(profile_name, data)
            self.status_label.setText(f"Imported {count} passwords from file")
        else:
            count = self.sync_manager.import_bookmarks(profile_name, data)
            self.status_label.setText(f"Imported {count} bookmarks from file")

        self.status_label.setStyleSheet(f"""
            color: {COLORS['accent']};
            font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
            font-size: {FONTS['size_sm']}px;
            padding: 4px;
        """)


class PasswordManagerDialog(QDialog):
    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self.setWindowTitle("Password Manager")
        self.setMinimumSize(700, 450)
        self.setStyleSheet(DIALOG_STYLE)
        self.showing_passwords = False
        self.setup_ui()
        self._load_passwords()
        self._handle_vault()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(_make_header("PASSWORD MANAGER"))

        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Profile:"))
        profile_row.addWidget(QLabel(LABEL_STYLE))
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(COMBO_STYLE)
        for name in self.sync_manager.get_profile_names():
            self.profile_combo.addItem(name)
        active = self.sync_manager.active_profile_name
        if active:
            idx = self.sync_manager.get_profile_names().index(active) if active in self.sync_manager.get_profile_names() else 0
            self.profile_combo.setCurrentIndex(idx)
        self.profile_combo.currentTextChanged.connect(self._load_passwords)
        profile_row.addWidget(self.profile_combo)
        profile_row.addStretch()

        self.toggle_show_btn = QPushButton("Show Passwords")
        self.toggle_show_btn.setStyleSheet(BTN_STYLE)
        self.toggle_show_btn.clicked.connect(self._toggle_show)
        profile_row.addWidget(self.toggle_show_btn)

        layout.addLayout(profile_row)

        # ── Vault (master-password encryption) status row ──
        vault_row = QHBoxLayout()
        self.vault_status = QLabel("")
        self.vault_status.setStyleSheet(f"""
            color: {COLORS['accent']};
            font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
            font-size: {FONTS['size_sm']}px;
        """)
        vault_row.addWidget(self.vault_status)
        vault_row.addStretch()

        self.set_vault_btn = QPushButton("Set Master Password...")
        self.set_vault_btn.setStyleSheet(BTN_STYLE)
        self.set_vault_btn.clicked.connect(self._set_master_password)
        vault_row.addWidget(self.set_vault_btn)

        self.change_vault_btn = QPushButton("Change Master Password...")
        self.change_vault_btn.setStyleSheet(BTN_STYLE)
        self.change_vault_btn.clicked.connect(self._change_master_password)
        vault_row.addWidget(self.change_vault_btn)

        self.lock_vault_btn = QPushButton("Lock Vault")
        self.lock_vault_btn.setStyleSheet(BTN_STYLE)
        self.lock_vault_btn.clicked.connect(self._lock_vault)
        vault_row.addWidget(self.lock_vault_btn)

        layout.addLayout(vault_row)

        self.search_edit = QLineEdit()
        self.search_edit.setStyleSheet(INPUT_STYLE)
        self.search_edit.setPlaceholderText("Search by URL or username...")
        self.search_edit.textChanged.connect(self._filter_passwords)
        layout.addWidget(self.search_edit)

        self.password_table = QTableWidget()
        self.password_table.setStyleSheet(TABLE_STYLE)
        self.password_table.setColumnCount(4)
        self.password_table.setHorizontalHeaderLabels(["URL", "Username", "Password", "Imported From"])
        self.password_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.password_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.password_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.password_table.verticalHeader().setVisible(False)
        layout.addWidget(self.password_table)

        btn_row = QHBoxLayout()

        add_btn = QPushButton("Add Password")
        add_btn.setStyleSheet(BTN_STYLE)
        add_btn.clicked.connect(self._add_password)
        btn_row.addWidget(add_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_elevated']};
                color: {COLORS['error']};
                border: 1px solid {COLORS['error']}40;
                padding: 6px 16px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['error']};
                background: {COLORS['error']}20;
            }}
        """)
        delete_btn.clicked.connect(self._delete_password)
        btn_row.addWidget(delete_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(BTN_STYLE)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
            font-size: {FONTS['size_xs']}px;
        """)
        layout.addWidget(self.count_label)

    def _handle_vault(self):
        """Reconcile the UI with the vault state (locked/unlocked/not enabled)."""
        sm = self.sync_manager
        if not sm.vault_enabled:
            self.vault_status.setText("\u26a0 Vault not enabled \u2014 passwords are stored UNENCRYPTED. "
                                      "Set a master password to protect them.")
            self.set_vault_btn.setVisible(True)
            self.change_vault_btn.setVisible(False)
            self.lock_vault_btn.setVisible(False)
            return
        if sm.is_vault_unlocked():
            self.vault_status.setText("\U0001f512 Vault unlocked \u2014 passwords are AES-256 encrypted at rest.")
            self.set_vault_btn.setVisible(False)
            self.change_vault_btn.setVisible(True)
            self.lock_vault_btn.setVisible(True)
            return
        # Vault enabled but locked -> prompt to unlock before showing anything
        self.vault_status.setText("\U0001f512 Vault is locked.")
        self.set_vault_btn.setVisible(False)
        self.change_vault_btn.setVisible(False)
        self.lock_vault_btn.setVisible(False)
        master, ok = QInputDialog.getText(
            self, "Unlock Vault", "Enter your master password:",
            echo=QLineEdit.Password,
        )
        if ok and sm.unlock_vault(master):
            self.vault_status.setText("\U0001f512 Vault unlocked \u2014 passwords are AES-256 encrypted at rest.")
            self.change_vault_btn.setVisible(True)
            self.lock_vault_btn.setVisible(True)
            self._load_passwords()
        else:
            QMessageBox.warning(
                self, "Vault Locked",
                "Vault could not be unlocked. Saved passwords remain hidden.",
            )
            self.reject()

    def _set_master_password(self):
        sm = self.sync_manager
        pw, ok = QInputDialog.getText(
            self, "Set Master Password",
            "Choose a master password. It encrypts ALL saved passwords (AES-256).\n"
            "It cannot be recovered if forgotten \u2014 write it down!",
            echo=QLineEdit.Password,
        )
        if not ok or not pw:
            return
        pw2, ok2 = QInputDialog.getText(
            self, "Confirm Master Password", "Repeat the master password:",
            echo=QLineEdit.Password,
        )
        if not ok2 or pw != pw2:
            QMessageBox.warning(self, "Set Master Password", "Passwords did not match.")
            return
        try:
            if sm.set_master_password(pw):
                self.vault_status.setText(
                    "\U0001f512 Vault enabled \u2014 passwords are AES-256 encrypted at rest."
                )
                self.set_vault_btn.setVisible(False)
                self.change_vault_btn.setVisible(True)
                self.lock_vault_btn.setVisible(True)
                self._load_passwords()
                QMessageBox.information(
                    self, "Vault Enabled", "All stored passwords have been encrypted."
                )
        except RuntimeError as e:
            QMessageBox.critical(self, "Vault Error", str(e))

    def _change_master_password(self):
        sm = self.sync_manager
        old, ok = QInputDialog.getText(
            self, "Change Master Password", "Current master password:",
            echo=QLineEdit.Password,
        )
        if not ok:
            return
        new, ok2 = QInputDialog.getText(
            self, "Change Master Password", "New master password:",
            echo=QLineEdit.Password,
        )
        if not ok2 or not new:
            return
        new2, ok3 = QInputDialog.getText(
            self, "Change Master Password", "Repeat new master password:",
            echo=QLineEdit.Password,
        )
        if not ok3 or new != new2:
            QMessageBox.warning(self, "Change Master Password", "New passwords did not match.")
            return
        if sm.change_master_password(old, new):
            self._load_passwords()
            QMessageBox.information(
                self, "Master Password Changed", "Vault re-keyed successfully."
            )
        else:
            QMessageBox.warning(
                self, "Change Master Password", "Current master password is incorrect."
            )

    def _lock_vault(self):
        self.sync_manager.lock_vault()
        self.vault_status.setText("\U0001f512 Vault is locked.")
        self.change_vault_btn.setVisible(False)
        self.lock_vault_btn.setVisible(False)
        self._load_passwords()

    def _load_passwords(self):
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return
        self.all_passwords = self.sync_manager.get_passwords(profile_name)
        self._refresh_table(self.all_passwords)

    def _refresh_table(self, passwords):
        self.password_table.setRowCount(len(passwords))
        for i, pw in enumerate(passwords):
            url_item = QTableWidgetItem(pw.get("url", ""))
            user_item = QTableWidgetItem(pw.get("username", ""))
            if self.showing_passwords:
                pass_item = QTableWidgetItem(pw.get("password", ""))
            else:
                pass_item = QTableWidgetItem("*" * min(len(pw.get("password", "")), 12))
            source_item = QTableWidgetItem(pw.get("imported_from", "manual"))

            for item in [url_item, user_item, pass_item, source_item]:
                item.setForeground(QColor(COLORS['text_primary']))
            self.password_table.setItem(i, 0, url_item)
            self.password_table.setItem(i, 1, user_item)
            self.password_table.setItem(i, 2, pass_item)
            self.password_table.setItem(i, 3, source_item)

        self.count_label.setText(f"{len(passwords)} password(s) stored")

    def _filter_passwords(self, text):
        if not text:
            self._refresh_table(self.all_passwords)
            return
        text_lower = text.lower()
        filtered = [
            pw for pw in self.all_passwords
            if text_lower in pw.get("url", "").lower()
            or text_lower in pw.get("username", "").lower()
        ]
        self._refresh_table(filtered)

    def _toggle_show(self):
        self.showing_passwords = not self.showing_passwords
        if self.showing_passwords:
            self.toggle_show_btn.setText("Hide Passwords")
        else:
            self.toggle_show_btn.setText("Show Passwords")
        self._refresh_table(self.all_passwords)

    def _add_password(self):
        from PySide6.QtWidgets import QInputDialog
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return

        url, ok = QInputDialog.getText(self, "Add Password", "URL:")
        if not ok or not url.strip():
            return
        username, ok = QInputDialog.getText(self, "Add Password", "Username:")
        if not ok:
            return
        password, ok = QInputDialog.getText(
            self, "Add Password", "Password:", echo=QLineEdit.Password
        )
        if not ok:
            return

        try:
            self.sync_manager.add_password(profile_name, url.strip(), username, password)
            self._load_passwords()
        except ValueError as e:
            QMessageBox.warning(self, "Vault Locked", str(e))

    def _delete_password(self):
        row = self.password_table.currentRow()
        if row < 0:
            return
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return

        url = self.password_table.item(row, 0).text()
        username = self.password_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Delete Password",
            f"Delete saved password for '{username}' on '{url}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.sync_manager.delete_password(profile_name, url, username)
            self._load_passwords()
