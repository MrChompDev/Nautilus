"""Certificate Search - The Depths

Real certificate-transparency search. Queries crt.sh's public JSON API for all
certificates Google/Certificate Transparency has recorded for a domain (the
same lookup CT lens / `stegosuite` recon does) to find subdomains and mail
servers that pDNS misses.

Kept kind: only queries the public transparency log; never scans hosts.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

CA_BASE = "https://crt.sh/?q={query}&output=json"


class CertWorker(QThread):
    found = Signal(str)
    error = Signal(str)
    done = Signal()

    def __init__(self, domain):
        super().__init__()
        self.domain = domain

    def run(self):
        q = urllib.parse.quote(f"%{self.domain}")
        url = CA_BASE.format(query=q)
        req = urllib.request.Request(url, headers={"User-Agent": "Nautilus-Depths/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read(4_000_000).decode("utf-8", errors="ignore")
        except Exception as e:
            self.error.emit(f"crt.sh query failed: {e}")
            self.done.emit()
            return
        try:
            entries = json.loads(raw)
        except json.JSONDecodeError:
            self.error.emit("crt.sh returned non-JSON (likely throttled); retry in a minute.")
            self.done.emit()
            return
        names = set()
        for e in entries:
            nm = e.get("name_value", "").replace("\n", "\x00").split("\x00")
            for n in nm:
                n = n.strip().lstrip("*.")
                if n and n.lower().endswith(self.domain.lower()):
                    names.add(n.lower())
        for n in sorted(names):
            self.found.emit(n)
        self.done.emit()


class CertSearchWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("Certificate Search - The Depths")
        self.resize(700, 580)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F512 Certificate Search",
            "Enumerate subdomains + hosts from Certificate Transparency logs"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Domain:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.domain = QLineEdit("google.com")
        self.domain.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.domain, 1)

        self.search_btn = QPushButton("\U0001F50D Search")
        self.search_btn.setStyleSheet(BTN_STYLE)
        self.search_btn.clicked.connect(self._search)
        row.addWidget(self.search_btn)
        layout.addLayout(row)

        self.hint = QLabel("Queries the public CT log at crt.sh (may take a few seconds).")
        self.hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(self.hint)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Certificate Search ready")

    def _log(self, msg, color=None):
        if color is not None:
            self.output.setTextColor(color)
        self.output.append(msg)

    def _search(self):
        domain = self.domain.text().strip().lower()
        if not domain:
            self._log("[!] Enter a domain")
            return
        self.output.clear()
        self._log(f"[*] Querying CT logs for certificates of '{domain}'...\n")
        self.search_btn.setEnabled(False)
        self.worker = CertWorker(domain)
        self.worker.found.connect(lambda n: self._log(f"    \U0001F512 {n}", color=GREEN))
        self.worker.error.connect(lambda e: self._log(f"[!] {e}", color=YELLOW))
        self.worker.done.connect(self._done)
        self.worker.start()

    def _done(self):
        self.search_btn.setEnabled(True)
        self._log("\n[*] Search complete.", color=CYAN)

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = CertSearchWindow(parent)
    win.show()
    return win