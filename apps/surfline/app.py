"""Surfline Browser App for Nautilus OS"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.theme import COLORS, FONTS, RADIUS_MD, RADIUS_SM


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

        layout.addWidget(nav)

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
                          outline: none;">
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
        self.url_bar.clear()

    def new_tab(self):
        self.home_page()

    def navigate(self):
        text = self.url_bar.text().strip()
        if "." in text and not text.startswith("http"):
            text = "https://" + text
        elif not text.startswith("http"):
            text = "https://www.google.com/search?q=" + text
        self.web.setUrl(QUrl(text))

    def update_url(self, url):
        self.url_bar.setText(url.toString())
