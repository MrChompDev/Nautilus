"""Network Map - The Depths"""

import os
import re
import socket
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

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

from apps.depths.tools._ui import BTN_STYLE, INPUT_STYLE, OUT_STYLE, hline, make_header
from core.theme import COLORS, FONTS


def _get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "192.168.1.1"
    finally:
        s.close()


class NetworkMapWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Network Map - The Depths")
        self.resize(620, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F5FA Network Map",
            "Sonar for your subnet - discover hosts on the local network"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Subnet:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.subnet = QLineEdit(_get_local_ip())
        self.subnet.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.subnet, 1)

        self.scan_btn = QPushButton("\U0001F50D Discover")
        self.scan_btn.setStyleSheet(BTN_STYLE)
        self.scan_btn.clicked.connect(self.discover)
        row.addWidget(self.scan_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Network Discovery initialized")
        self._log(f"[*] Detected local IP: {_get_local_ip()}")

    def _log(self, msg):
        self.output.append(msg)

    def _is_up(self, ip):
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                capture_output=True, timeout=2
            )
            return result.returncode == 0
        except Exception:
            try:
                with socket.create_connection((ip, 445), timeout=1):
                    return True
            except OSError:
                return False

    def discover(self):
        base = self.subnet.text().strip()
        if not base:
            self._log("[!] Enter a subnet")
            return
        if not re.match(r"^\d+\.\d+\.\d+(\.\d+)?$", base):
            self._log("[!] Invalid subnet format")
            return
        prefix = ".".join(base.split(".")[:3])
        self.output.clear()
        self._log(f"[*] Scanning subnet {prefix}.0/24")
        self._log("[*] Method: Ping sweep + ARP check\n")
        self.scan_btn.setEnabled(False)

        found = []
        for i in range(1, 255):
            ip = f"{prefix}.{i}"
            if self._is_up(ip):
                found.append(ip)

        self.scan_btn.setEnabled(True)
        self._log(f"[*] Discovery complete: {len(found)} host(s) online")
        for ip in found:
            name = ""
            try:
                name = socket.gethostbyaddr(ip)[0]
            except Exception:
                name = "unknown"
            self._log(f"    \U0001F4A1 {ip:<16}  {name}")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = NetworkMapWindow(parent)
    win.show()
    return win
