"""WHOIS Lookup - The Depths"""

import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, INPUT_STYLE, OUT_STYLE, hline, make_header
from core.theme import COLORS, FONTS

# IANA WHOIS server - reliable, doesn't require a package
IANA_WHOIS = "whois.iana.org"


def _whois_query(domain, server="whois.iana.org", port=43):
    try:
        ip = socket.gethostbyname(server)
        with socket.create_connection((ip, port), timeout=8) as s:
            s.sendall(f"{domain}\r\n".encode())
            data = b""
            while True:
                chunk = s.recv(65535)
                if not chunk:
                    break
                data += chunk
                if len(data) > 100000:
                    break
            return data.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error: {e}"


class WhoisWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WHOIS Lookup - The Depths")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F3D8 WHOIS Lookup",
            "Domain registration records - query the public registry"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Domain:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.domain = QLineEdit("example.com")
        self.domain.setPlaceholderText("example.com")
        self.domain.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.domain, 1)

        self.lookup_btn = QPushButton("\U0001F50D Lookup")
        self.lookup_btn.setStyleSheet(BTN_STYLE)
        self.lookup_btn.clicked.connect(self.lookup)
        row.addWidget(self.lookup_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] WHOIS Lookup ready")
        self._log(f"[*] Querying IANA WHOIS server ({IANA_WHOIS})")

    def _log(self, msg):
        self.output.append(msg)

    def lookup(self):
        domain = self.domain.text().strip()
        if not domain:
            self._log("[!] Enter a domain")
            return
        self.output.clear()
        self._log(f"[*] Querying {IANA_WHOIS} for {domain}...")
        self.lookup_btn.setEnabled(False)
        result = _whois_query(domain)
        self.lookup_btn.setEnabled(True)

        if result.startswith("Error"):
            self._log(f"[!] {result}")
            return

        # Try to find the referral WHOIS server for the TLD
        referral = None
        for line in result.splitlines():
            if "whois:" in line.lower():
                ref = line.split(":")[1].strip()
                if ref:
                    referral = ref
                    break

        self._log(result)

        if referral:
            self._log(f"\n[*] Found registrar WHOIS server: {referral}")
            self._log(f"[*] Querying {referral} for detailed info...\n")
            detailed = _whois_query(domain, referral)
            self._log(detailed)

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = WhoisWindow(parent)
    win.show()
    return win
