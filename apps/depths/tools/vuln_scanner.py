"""Vulnerability Scanner - The Depths"""

import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

# Simulated vulnerability signatures keyed by (port, service)
SIGS = {
    21:  [("vsftpd 2.3.4", "Critical", "Backdoor - RCE possible"),],
    22:  [("OpenSSH < 7.4", "Medium", "User enumeration"),],
    23:  [("Telnet cleartext", "High", "Credentials sent unencrypted"),],
    80:  [("Apache 2.4.49", "Critical", "Path traversal (CVE-2021-41773)"),],
    443: [("OpenSSL < 1.1.1", "Medium", "Heartbleed-era TLS vuln"),],
    3306:[("MySQL 5.5", "Medium", "Outdated version, known CVEs"),],
    3389:[("RDP NLA disabled", "High", "BlueKeep susceptible"),],
    445: [("SMBv1", "Critical", "EternalBlue susceptible"),],
    8080:[("Tomcat manager exposed", "High", "Default creds possible"),],
}


class VulnScanWorker(QThread):
    result = Signal(int, str, str, str)
    finished = Signal()
    log = Signal(str)

    def __init__(self, host, ports):
        super().__init__()
        self.host = host
        self.ports = ports

    def run(self):
        for port in self.ports:
            try:
                with socket.create_connection((self.host, port), timeout=2) as _:
                    if port in SIGS:
                        for name, sev, desc in SIGS[port]:
                            self.result.emit(port, name, sev, desc)
                    else:
                        self.result.emit(port, "Unknown service", "Info", "Check manually")
            except OSError:
                self.log.emit(f"  [!] Port {port}: closed")
        self.finished.emit()


class VulnScannerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("Vulnerability Scanner - The Depths")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F9F1 Vulnerability Scanner",
            "Find cracks in the hull - detect known vulnerabilities"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Target:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.target = QLineEdit("127.0.0.1")
        self.target.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.target, 1)

        self.scan_btn = QPushButton("\U0001F50D Scan")
        self.scan_btn.setStyleSheet(BTN_STYLE)
        self.scan_btn.clicked.connect(self.start)
        row.addWidget(self.scan_btn)
        layout.addLayout(row)

        hint = QLabel("Demo mode: scans common ports against a local signature database.")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(hint)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Vulnerability Scanner ready")
        self._log(f"[*] {len(SIGS)} signatures loaded in local database")

    def _log(self, msg):
        self.output.append(msg)

    def start(self):
        host = self.target.text().strip()
        if not host:
            self._log("[!] Enter a target")
            return
        self.output.clear()
        self._log(f"[*] Scanning {host} for known vulnerabilities...\n")
        self.scan_btn.setEnabled(False)
        self.worker = VulnScanWorker(host, sorted(SIGS.keys()))
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(self._done)
        self.worker.log.connect(self._log)
        self.worker.start()

    def _on_result(self, port, name, sev, desc):
        color = RED if sev == "Critical" else YELLOW if sev in ("High", "Medium") else GREEN
        self.output.setTextColor(color)
        self._log(f"  [{sev.upper():<8}] Port {port:<5} {name}")
        self._log(f"      {desc}")

    def _done(self):
        self.scan_btn.setEnabled(True)
        self.output.setTextColor(YELLOW)
        self._log("\n[*] Scan complete. Review findings by severity.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = VulnScannerWindow(parent)
    win.show()
    return win
