"""Surfline Browser App for Nautilus OS"""

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QWidget

from apps.surfline.interceptor import AdBlocker
from apps.surfline.search import results_to_html, search
from apps.surfline.vault import find_entry
from apps.surfline.vaultui import SavePasswordDialog, VaultWindow, ensure_account
from core.theme import COLORS, FONTS, RADIUS_SM


class SurflineWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Surfline")
        self.resize(1024, 680)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_light']};
            }}
        """)

        # Main layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Tab bar ──
        self.tabs = QFrame()
        self.tabs.setFixedHeight(36)
        self.tabs.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_dark']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        self.tab_layout = QHBoxLayout(self.tabs)
        self.tab_layout.setContentsMargins(8, 0, 8, 0)
        self.tab_layout.setSpacing(2)
        self.tab_layout.addStretch()

        new_tab = QPushButton("+")
        new_tab.setFixedSize(28, 24)
        new_tab.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_mid']};
                color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['hover']};
            }}
        """)
        new_tab.clicked.connect(self.new_tab)
        self.tab_layout.addWidget(new_tab)

        layout.addWidget(self.tabs)

        # ── Navigation bar ──
        nav = QFrame()
        nav.setFixedHeight(44)
        nav.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_mid']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(4)

        btn_style = f"""
            QPushButton {{
                background: {COLORS['bg_dark']};
                color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_SM};
                font-size: {FONTS['size_sm']}px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background: {COLORS['hover']};
            }}
        """

        back = QPushButton("<")
        back.setFixedSize(30, 28)
        back.setStyleSheet(btn_style)
        back.clicked.connect(lambda: self.web.back())
        nav_layout.addWidget(back)

        forward = QPushButton(">")
        forward.setFixedSize(30, 28)
        forward.setStyleSheet(btn_style)
        forward.clicked.connect(lambda: self.web.forward())
        nav_layout.addWidget(forward)

        refresh = QPushButton("↻")
        refresh.setFixedSize(30, 28)
        refresh.setStyleSheet(btn_style)
        refresh.clicked.connect(lambda: self.web.reload())
        nav_layout.addWidget(refresh)

        # URL bar
        self.url_bar = QLineEdit()
        self.showing_search = False
        self.url_bar.setPlaceholderText("Search or enter URL...")
        self.url_bar.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg_light']};
                color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_SM};
                padding: 4px 10px;
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['coral']};
            }}
        """)
        self.url_bar.returnPressed.connect(self.navigate)
        nav_layout.addWidget(self.url_bar)

        home = QPushButton("⌂")
        home.setFixedSize(30, 28)
        home.setStyleSheet(btn_style)
        home.clicked.connect(self.home_page)
        nav_layout.addWidget(home)

        vault_btn = QPushButton("🔒")
        vault_btn.setFixedSize(34, 28)
        vault_btn.setStyleSheet(btn_style)
        vault_btn.clicked.connect(self.open_vault)
        nav_layout.addWidget(vault_btn)

        layout.addWidget(nav)
        # Ad & tracker blocker
        profile = QWebEngineProfile.defaultProfile()
        self.adblocker = AdBlocker()
        profile.setUrlRequestInterceptor(self.adblocker)
        # ── Web view (create BEFORE home_page) ──
        self.web = QWebEngineView()
        self.web.urlChanged.connect(self.update_url)
        layout.addWidget(self.web)

        # Load home page
        self.home_page()

    def home_page(self):
        html = f"""
        <html>
        <body style="background-color: {COLORS['bg_light']}; display: flex; flex-direction: column;
                     align-items: center; justify-content: center; height: 100vh; margin: 0;
                     font-family: '{FONTS['mono']}';">
            <h1 style="color: {COLORS['text_dark']}; font-size: 36px; margin-bottom: 20px;">Surfline</h1>
            <p style="color: {COLORS['text_muted']}; margin-bottom: 30px;">Your gateway to the web</p>
            <input type="text" placeholder="Search or enter URL..."
                style="width: 500px; padding: 12px 16px; font-size: 14px;
              border: 2px solid {COLORS['border']}; border-radius: 8px;
              background: {COLORS['bg_light']}; color: {COLORS['text_dark']};
              outline: none;"
            <div style="display: flex; gap: 20px; margin-top: 40px;">
                <a href="https://www.google.com" style="color: {COLORS['coral']}; text-decoration: none; font-size: 14px;">Google</a>
                <a href="https://www.youtube.com" style="color: {COLORS['coral']}; text-decoration: none; font-size: 14px;">YouTube</a>
                <a href="https://www.github.com" style="color: {COLORS['coral']}; text-decoration: none; font-size: 14px;">GitHub</a>
                <a href="https://www.wikipedia.org" style="color: {COLORS['coral']}; text-decoration: none; font-size: 14px;">Wikipedia</a>
            </div>
        </body>
        </html>
        """
        self.web.setHtml(html)
        self.showing_search = False
        self.url_bar.clear()

    def new_tab(self):
        self.home_page()

    def open_vault(self):
        passphrase = ensure_account(self)
        if passphrase is None:
            return
        win = VaultWindow(passphrase)
        win.show()

    def save_password(self):
        site = self.web.url().toString()
        passphrase = ensure_account(self)
        if passphrase is None:
            return
        dlg = SavePasswordDialog(site=site, parent=self)
        if dlg.exec() == QDialog.Accepted:
            s, u, p = dlg.values()
            from apps.surfline.vault import add_entry
            add_entry(passphrase, s, u, p)

    def autofill(self):
        passphrase = ensure_account(self)
        if passphrase is None:
            return
        site = self.web.url().toString()
        entry = find_entry(passphrase, site)
        if entry is None:
            return
        self.web.page().runJavaScript(f"""
            document.querySelector('input[type=password]').value = '{entry['password']}';
        """)

    def navigate(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        # If it looks like a URL, go there directly
        if "." in text and not text.startswith("http"):
            text = "https://" + text
            self.web.setUrl(QUrl(text))
        elif text.startswith("http"):
            self.web.setUrl(QUrl(text))
        else:
            # It's a search query
            results = search(text)
            html = results_to_html(text, results, COLORS, FONTS)
            self.web.setHtml(html)
            self.showing_search = True

    def update_url(self, url):
        if not self.showing_search and not url.toString().startswith("data:"):
            self.url_bar.setText(url.toString())
        self.setWindowTitle(f"Surfline — {self.adblocker.blocked_count} blocked")
