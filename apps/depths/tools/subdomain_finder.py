"""Subdomain Finder - The Depths"""

import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, INPUT_STYLE, OUT_STYLE, hline, make_header
from core.theme import COLORS, FONTS

COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "dev", "staging", "api", "blog", "shop",
    "admin", "portal", "vpn", "webmail", "ns1", "ns2", "mx", "smtp",
    "pop", "imap", "cdn", "static", "img", "assets", "docs", "help",
    "support", "forum", "test", "beta", "demo", "app", "secure", "login",
    "auth", "gateway", "intranet", "remote", "cpanel", "whm", "status",
    "statuspage", "dashboard", "tracking", "analytics", "monitoring",
    "grafana", "jenkins", "git", "gitlab", "svn", "ci", "build",
]

WORDLIST_SIZES = {
    "Small (40)":   40,
    "Medium (100)": 100,
    "Large (all)":  len(COMMON_SUBDOMAINS),
}


class SubdomainWorker(QThread):
    found = Signal(str, str)
    checked = Signal(int)
    finished = Signal()
    log = Signal(str)

    def __init__(self, domain, words):
        super().__init__()
        self.domain = domain
        self.words = words
        self._running = True

    def run(self):
        total = len(self.words)
        for i, sub in enumerate(self.words):
            if not self._running:
                break
            full = f"{sub}.{self.domain}"
            try:
                infos = socket.getaddrinfo(full, None)
                ip = infos[0][4][0]
                self.found.emit(full, ip)
            except socket.gaierror:
                pass
            except OSError:
                pass
            self.checked.emit(int((i + 1) / total * 100))
        self.finished.emit()

    def stop(self):
        self._running = False


class SubdomainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.found_count = 0
        self.setWindowTitle("Subdomain Finder - The Depths")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F3DC Subdomain Finder",
            "Probe common subdomains for hidden services"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Domain:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.domain = QLineEdit("example.com")
        self.domain.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.domain, 1)

        self.wordlist = QComboBox()
        self.wordlist.addItems(WORDLIST_SIZES.keys())
        self.wordlist.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        row.addWidget(self.wordlist)

        self.scan_btn = QPushButton("\U0001F50D Probe")
        self.scan_btn.setStyleSheet(BTN_STYLE)
        self.scan_btn.clicked.connect(self.start)
        row.addWidget(self.scan_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Subdomain Finder ready")
        self._log(f"[*] Wordlist: {len(COMMON_SUBDOMAINS)} common subdomains available")

    def _log(self, msg):
        self.output.append(msg)

    def start(self):
        domain = self.domain.text().strip()
        if not domain:
            self._log("[!] Enter a domain")
            return
        size = WORDLIST_SIZES[self.wordlist.currentText()]
        words = COMMON_SUBDOMAINS[:size]
        self.output.clear()
        self._log(f"[*] Probing {len(words)} subdomains of {domain}...\n")
        self.found_count = 0
        self.scan_btn.setEnabled(False)

        self.worker = SubdomainWorker(domain, words)
        self.worker.found.connect(self._on_found)
        self.worker.finished.connect(self._done)
        self.worker.log.connect(self._log)
        self.worker.start()

    def _on_found(self, full, ip):
        self.found_count += 1
        self._log(f"    \u2714 {full:<40} -> {ip}")

    def _done(self):
        self.scan_btn.setEnabled(True)
        self._log(f"\n[*] Probe complete: {self.found_count} subdomain(s) resolved")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        super().closeEvent(event)


def run(parent=None):
    win = SubdomainWindow(parent)
    win.show()
    return win
