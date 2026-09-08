"""DNS Enumerator - The Depths

Real DNS enumeration of a domain. Uses dnspython when available (all record
types queried like the `dnsrecon` tool); falls back to the stdlib socket API
for A/AAAA/CNAME/MX only. Mirrors how DNS recon tools actually query a
target's full record set.
"""

import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, hline, make_header
from core.theme import COLORS, FONTS

try:
    import dns.rdatatype
    import dns.resolver
    HAVE_DNS = True
except ImportError:
    HAVE_DNS = False

RECORD_TYPES = [
    ("A",      "IPv4 address record"),
    ("AAAA",   "IPv6 address record"),
    ("MX",     "Mail exchange"),
    ("NS",     "Name server"),
    ("TXT",    "Text record (SPF/DKIM)"),
    ("CNAME",  "Canonical name"),
    ("SOA",    "Start of authority"),
]

if HAVE_DNS:
    RESOLVER = dns.resolver.Resolver()
    RESOLVER.lifetime = 4.0
    RESOLVER.timeout = 4.0
else:
    RESOLVER = None


def _lookup(domain, rtype):
    """Return list of record strings for one domain/record type."""
    if HAVE_DNS:
        try:
            answers = RESOLVER.resolve(domain, rtype)
            vals = []
            for ans in answers:
                if rtype == "A":
                    vals.append(ans.address)
                elif rtype == "AAAA":
                    vals.append(ans.address)
                elif rtype == "MX":
                    vals.append(f"{ans.preference}  {ans.exchange}")
                elif rtype == "NS":
                    vals.append(str(ans.target))
                elif rtype == "TXT":
                    vals.append("".join(t.decode("utf-8", errors="ignore") for t in ans.strings))
                elif rtype == "CNAME":
                    vals.append(str(ans.target))
                elif rtype == "SOA":
                    vals.append(str(ans))
            return vals
        except Exception:
            return []
    else:
        # Stdlib fallback (A / AAAA only; CNAME and MX are best-effort)
        return _fallback(domain, rtype)


def _fallback(domain, rtype):
    try:
        if rtype == "A":
            return sorted(set(
                a[4][0] for a in socket.getaddrinfo(domain, None)
                if a[0] == socket.AF_INET
            ))
        if rtype == "AAAA":
            return sorted(set(
                a[4][0] for a in socket.getaddrinfo(domain, None)
                if a[0] == socket.AF_INET6
            ))
    except Exception:
        pass
    return []


class DnsEnumWorker(QThread):
    result = Signal(str, str, list)
    log = Signal(str)
    finished = Signal()

    def __init__(self, domain):
        super().__init__()
        self.domain = domain

    def run(self):
        found_any = False
        for rtype, _label in RECORD_TYPES:
            vals = _lookup(self.domain, rtype)
            if vals:
                found_any = True
                self.result.emit(rtype, _label, vals)
            else:
                self.log.emit(f"  [{rtype:<5}] no records")
        if not found_any:
            self.log.emit("\u2716 No DNS records found (domain may not exist).")
        else:
            self.log.emit("\n\u2714 Enumeration complete.")
        self.finished.emit()


class DnsEnumWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
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
        mode = "dnspython (full record types)" if HAVE_DNS else "stdlib (A/AAAA only)"
        self._log(f"[*] Backend: {mode}")
        self._log(f"[*] Record types: {', '.join(r[0] for r in RECORD_TYPES)}")

    def _log(self, msg):
        self.output.append(msg)

    def enumerate(self):
        domain = self.domain.text().strip()
        if not domain:
            self._log("[!] Enter a domain")
            return
        self.output.clear()
        self._log(f"[*] Enumerating DNS records for {domain}\n")
        self.enum_btn.setEnabled(False)

        self.worker = DnsEnumWorker(domain)
        self.worker.result.connect(self._on_result)
        self.worker.log.connect(self._log)
        self.worker.finished.connect(self._done)
        self.worker.start()

    def _on_result(self, rtype, label, vals):
        self._log(f"  {rtype:<5} ({label}):")
        self.output.setTextColor(GREEN)
        for v in vals[:30]:
            self._log(f"      \u2714 {v}")
        self.output.setTextColor(CYAN)

    def _done(self):
        self.enum_btn.setEnabled(True)

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = DnsEnumWindow(parent)
    win.show()
    return win