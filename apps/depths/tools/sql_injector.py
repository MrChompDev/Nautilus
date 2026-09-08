"""SQL Injector - The Depths (educational/demo)"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

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

# Educational SQL injection payloads
PAYLOADS = [
    ("Classic OR 1=1",              "' OR 1=1 --"),
    ("Comment bypass",              "'--"),
    ("Union select",                "' UNION SELECT NULL, NULL, NULL --"),
    ("Boolean blind",               "' AND 1=1 --"),
    ("Boolean blind (false)",       "' AND 1=2 --"),
    ("Time-based blind",            "' OR SLEEP(5) --"),
]


class SqlInjectorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SQL Injector - The Depths (Educational)")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4A5 SQL Injector",
            "Test web inputs for SQL injection (interactive sandbox)"
        ))
        layout.addWidget(hline())

        warn = QLabel("\u26A0 Use only on your own lab targets. Real exploitation is illegal without authorization.")
        warn.setWordWrap(True)
        warn.setStyleSheet(f"color: {COLORS['warning']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(warn)

        row = QHBoxLayout()
        lbl = QLabel("URL:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.url = QLineEdit("http://localhost:8000/search?q=apples")
        self.url.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.url, 1)
        layout.addLayout(row)

        self.payload = QComboBox()
        self.payload.addItems([f"{name}  ->  {sql}" for name, sql in PAYLOADS])
        self.payload.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        layout.addWidget(self.payload)

        row2 = QHBoxLayout()
        self.test_btn = QPushButton("\U0001F4A5 Send Test")
        self.test_btn.setStyleSheet(BTN_STYLE)
        self.test_btn.clicked.connect(self._test)
        row2.addWidget(self.test_btn)

        self.check_btn = QPushButton("Explain")
        self.check_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.check_btn.clicked.connect(self._explain)
        row2.addWidget(self.check_btn)
        row2.addStretch()
        layout.addLayout(row2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] SQL Injector ready (educational)")
        self._log("[*] Learn how query injection works without touching real targets.")

    def _log(self, msg):
        self.output.append(msg)

    def _test(self):
        base = self.url.text().strip()
        if not base:
            self._log("[!] Enter a URL template")
            return
        sel = self.payload.currentText()
        name, sql = [x.strip() for x in sel.split("->")]
        self.output.clear()
        self._log(f"[*] Payload: {name}")
        self._log(f"[*] Injection string: {sql}\n")
        self._log("[*] The backend would execute (conceptually):")
        self._log(f"    SELECT * FROM products WHERE name = '{sql}'")
        self._log("\n[+] If the app is vulnerable, the query returns:\n")
        self._log("    - ALL rows (OR 1=1 always true)")
        self._log("    - Extra columns (UNION SELECT)")
        self._log("    - Delayed response (SLEEP)")
        self._log("\n[*] In the sandbox, only CONCEPT exposure is demonstrated.")
        self._log("[*] Defending: use parameterized queries + input sanitization.")

    def _explain(self):
        self.output.clear()
        self._log("[*] How SQL injection works:\n")
        self._log("  1. App builds SQL by concatenating user input:")
        self._log("     SELECT * FROM users WHERE user = '" + "' + input")
        self._log("\n  2. Attacker supplies: ' OR 1=1 --")
        self._log("     The app builds: SELECT * FROM users WHERE user = '' OR 1=1 --'")
        self._log("\n  3. 'OR 1=1' is always true -> returns ALL rows")
        self._log("     '--' comments out the trailing quote\n")
        self._log("[*] Prevention:\n")
        self._log("     - Parameterized/prepared statements")
        self._log("     - Input validation and output encoding")
        self._log("     - Least-privilege DB accounts")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = SqlInjectorWindow(parent)
    win.show()
    return win
