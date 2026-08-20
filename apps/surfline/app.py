"""Surfline Browser App for Nautilus OS"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
import core
from core.main import NautilusShell, COLORS, FONTS, RADIUS_MD, RADIUS_SM


class SurflineWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Surfline Browser")
        self.resize(1024, 680)
        self.setStyleSheet(f"""
        QMainWindow {{
            background-color: {COLORS['bg_light']};
            }}
        """)

        # Main Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Navigation Bar
        nav = QFrame()
        nav.setFixedHeight(44)
        nav.setStyleSheet(f"""
            QFrame{{
            background: {COLORS['bg_mid']};
            }}
        """)
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(4)

        btn_style = f"""
            QPushButton {{
                background: {COLORS['bg_dark']};
                color: {COLORS['text_dark']}
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_SM}
                font-size: {FONTS['size_sm']}px;
                padding: 4px 10px;
                }}
            
            QPushButton:hover {{
                background: {COLORS['hover']};
            }}"""

        back = QPushButton("<")
        back.setFixedSize(30, 28)
        back.setStyleSheet(btn_style)
        back.clicked.connect(lambda: self.web.back())
        nav_layout.addWidget(back)

        forward = QPushButton (">")
        forward.setFixedSize(30, 28)
        forward.setStyleSheet(btn_style)
        forward.clicked.connect(lambda: self.web.forward())

        refresh = QPushButton ("↻")
        refresh.setFixedSize(30, 28)
        refresh.setStyleSheet(btn_style)
        refresh.clicked.connect(lambda: self.web.refresh())
        nav_layout.addWidget(refresh)

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or Enter URL")
        self.url_bar.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg_light']};
                color: {COLORS['text_dark']}
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_SM};
                padding: 4px 10px;
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
            }}
            QLineEdit:focus {{
                border: 1px soild {COLORS['coral']};
            }}
        """)
        self.url_bar.returnPressed.connect(self.navigate)
        nav_layout.addWidget(self.url_bar)

        home = QPushButton ("⌂")
        home.setFixedSize(30, 28)
        home.setStyleSheet(btn_style)
        home.clicked.connect(lambda: self.web.setURL(QUrl("https://www.google.com")))
        nav_layout.addWidget(home)

        # Web View (going to build a custom search engine later down the line so it doesn't use google)
        self.web = QWebEngineView()
        self.web.setUrl(QUrl("https://google.com"))
        self.web.urlChanged.connect(self.update_url)
        layout.addWidget(self.web)

    def navigate(self):
        text = self.url_bar.text().strip()
        if "." in text and not text.startwith("http"):
            text = "https://" + text
        elif not text.startwith("http"):
            text = "https://www.google.com/search?q=" + text
        self.web.setURL(QUrl(text))

    def update_url(self, url):
        self.url_bar.setText(url.toString())
