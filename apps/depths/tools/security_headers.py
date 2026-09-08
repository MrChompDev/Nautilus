"""Security Headers - The Depths

Real HTTP security-header audit. Does a get request to a URL (redirects
followed, ~5s), then grades absence/presence of the headers OWASP recommends.
This is the same check the site securityheaders.com runs, done politely for a
single URL.
"""

import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

HEADERS = [
    ("Content-Security-Policy", "Blocks XSS/injection with a source allowlist", "High"),
    ("X-Frame-Options", "Prevents clickjacking", "High"),
    ("X-Content-Type-Options", "Stops MIME sniffing (nosniff)", "Medium"),
    ("Strict-Transport-Security", "Forces HTTPS (HSTS)", "High"),
    ("Referrer-Policy", "Limits referrer leakage", "Low"),
    ("Permissions-Policy", "Restricts browser features (camera, geo)", "Medium"),
    ("X-XSS-Protection", "Legacy IE/XSS filter (now deprecated)", "Low"),
]


class HeadersWorker(QThread):
    result = Signal(dict)
    error = Signal(str)
    done = Signal()

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        req = urllib.request.Request(self.url, headers={"User-Agent": UA, "Accept": "text/html"})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                received = {k.lower(): v for k, v in resp.headers.items()}
                self.result.emit({"final": resp.geturl(), "status": resp.getcode(), "headers": received})
        except urllib.error.HTTPError as e:
            # some servers reply with 403/301 + headers - still read them
            self.result.emit({"final": e.url if "url" in dir(e) else self.url, "status": e.code, "headers": {b.lower(): a for a, b in e.headers.items()}})
        except Exception as e:
            self.error.emit(f"Request failed: {type(e).__name__}: {e}")
        self.done.emit()


class HeadersWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("Security Headers - The Depths")
        self.resize(760, 600)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F512 Security Headers",
            "Grade a site's HTTP security headers (OWASP baseline)"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("URL:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.url = QLineEdit("https://google.com")
        self.url.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.url, 1)

        self.run_btn = QPushButton("\U0001F50D Check")
        self.run_btn.setStyleSheet(BTN_STYLE)
        self.run_btn.clicked.connect(self._check)
        row.addWidget(self.run_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Security Headers ready - real GET request, OWASP grading.")

    def _log(self, msg, color=None):
        if color is not None:
            self.output.setTextColor(color)
        self.output.append(msg)

    def _check(self):
        url = self.url.text().strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.output.clear()
        self._log(f"[*] Checking {url}...\n")
        self.run_btn.setEnabled(False)
        self.worker = HeadersWorker(url)
        self.worker.result.connect(self._render)
        self.worker.error.connect(lambda e: self._log(f"[!] {e}", color=RED))
        self.worker.done.connect(lambda: self.run_btn.setEnabled(True))
        self.worker.start()

    def _render(self, res):
        headers = res["headers"]
        present = set()
        self._log(f"[*] Final URL: {res['final']}  (HTTP {res['status']})\n", color=CYAN)
        missing = []
        for name, why, sev in HEADERS:
            lower = name.lower()
            if any(k == lower for k in headers):
                present.add(name)
                val = headers[lower][:80]
                color = GREEN if sev == "Medium" else GREEN
                self._log(f"    [\u2714] {name}: {val}", color=color)
            else:
                missing.append((name, why, sev))
                color = RED if sev == "High" else YELLOW
                self._log(f"    [\u2718] {name}  -  ({why})", color=color)

        if not present:
            self._log("\n[*] No standard security headers found at all!", color=RED)
        else:
            score = round(len(present) / len(HEADERS) * 100)
            self._log(f"\n[*] Score: {score}/100 ({len(present)} of {len(HEADERS)} present)", color=GREEN if score >= 60 else YELLOW)
        self._log("\n[!] Grades are a baseline - always review CSP directives in detail.", color=YELLOW)

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = HeadersWindow(parent)
    win.show()
    return win