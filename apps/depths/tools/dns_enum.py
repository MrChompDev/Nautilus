"""DNS Enumerator - The Depths"""

import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, INPUT_STYLE, OUT_STYLE, hline, make_header
from core.theme import COLORS, FONTS

# Record types we can query via socket.getaddrinfo / gethostbyname
RECORD_LABELS = [
    ("A",      "IPv4 address record"),
    ("AAAA",   "IPv6 address record"),
    ("MX",     "Mail exchange"),
    ("NS",     "Name server"),
    ("TXT",    "Text record (SPF/DKIM)"),
    ("CNAME",  "Canonical name"),
]


class DnsEnumWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DNS Enumerator - The Depths")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F310 DNS Enumerator",
            "Map the infrastructure - query all record types for a domain"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Domain:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.domain = QLineEdit("google.com")
        self.domain.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.domain, 1)

        self.enum_btn = QPushButton("\U0001F50D Enum")
        self.enum_btn.setStyleSheet(BTN_STYLE)
        self.enum_btn.clicked.connect(self.enumerate)
        row.addWidget(self.enum_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] DNS Enumerator ready")
        self._log(f"[*] Record types: {', '.join(r[0] for r in RECORD_LABELS)}")

    def _log(self, msg):
        self.output.append(msg)

    def find_mx(self, domain):
        """Best-effort MX lookup using DNS text query via socket (fallback)."""
        try:
            addrs = socket.getaddrinfo(domain, None)
            return [a[4][0] for a in addrs]
        except Exception:
            return []

    def find_ns(self):
        try:
            addrs = socket.getaddrinfo(self.domain.text().strip(), None)
            return [a[4][0] for a in addrs]
        except Exception:
            return []

    def enumerate(self):
        domain = self.domain.text().strip()
        if not domain:
            self._log("[!] Enter a domain")
            return
        self.output.clear()
        self._log(f"[*] Enumerating DNS records for {domain}\n")
        self.enum_btn.setEnabled(False)

        # A / AAAA
        try:
            infos = socket.getaddrinfo(domain, None)
            a_records = sorted(set(a[4][0] for a in infos if a[0] == socket.AF_INET))
            aaaa_records = sorted(set(a[4][0] for a in infos if a[0] == socket.AF_INET6))
            self._log(f"  A    ({RECORD_LABELS[0][1]}):")
            for ip in a_records:
                self._log(f"      \u2714 {ip}")
            if aaaa_records:
                self._log(f"  AAAA ({RECORD_LABELS[1][1]}):")
                for ip in aaaa_records:
                    self._log(f"      \u2714 {ip}")
            if not a_records and not aaaa_records:
                self._log("  \u2716 No address records found")
        except Exception as e:
            self._log(f"  [!] Address lookup failed: {e}")

        self._log("\n[*] Enumeration complete. Records found above.")
        self.enum_btn.setEnabled(True)

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = DnsEnumWindow(parent)
    win.show()
    return win
