"""Network Map - The Depths

Real subnet discovery, three layers like a real mapper tool:
1. ARP sweep via scapy (fast, finds hosts behind ICMP filters) when available.
2. Local ARP cache read (instant, no packets sent).
3. Ping sweep fallback (any host blocks - tried per-host only when needed).

Each discovered host gets real reverse-DNS / hostname lookup.
"""

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

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, hline, make_header
from core.theme import COLORS, FONTS

try:
    from scapy.all import ARP, Ether, srp
    HAVE_SCAPY = True
except ImportError:
    HAVE_SCAPY = False


def _get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "192.168.1.1"
    finally:
        s.close()


def _arp_sweep(prefix):
    """ARP sweep with scapy; return {ip: mac}."""
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=f"{prefix}.0/24"), timeout=3, verbose=False)
    return {rcv.psrc: rcv.hwsrc for _, rcv in ans}


def _arp_cache():
    """Read system ARP table; return {ip: mac}."""
    rows = {}
    for path in ("/proc/net/arp",):
        try:
            with open(path) as f:
                next(f, None)
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[0] != "IP":
                        rows[parts[0]] = parts[3]
        except OSError:
            continue
    return rows


def _is_up_ping(ip):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True, timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False


class NetworkMapWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Network Map - The Depths")
        self.resize(680, 580)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F5FA Network Map",
            "Sonar for your subnet - ARP sweep + ping fallback"
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

        hint = QLabel("Backend: scapy ARP sweep" if HAVE_SCAPY else "Backend: ARP cache + ping sweep (scapy not installed)")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(hint)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Network Discovery initialized")
        self._log(f"[*] Detected local IP: {_get_local_ip()}")

    def _log(self, msg, color=None):
        if color is not None:
            self.output.setTextColor(color)
        self.output.append(msg)

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
        self.scan_btn.setEnabled(False)

        found = {}

        if HAVE_SCAPY:
            self._log(f"[*] ARP-sweeping {prefix}.0/24 via scapy...")
            try:
                found = _arp_sweep(prefix)
            except Exception as e:
                self._log(f"[!] ARP sweep failed ({e}); falling back.")
                found = {}

        if not found:
            # instant local ARP cache pass
            cache = _arp_cache()
            for ip, mac in cache.items():
                if ip.startswith(prefix):
                    found[ip] = mac
            if found:
                self._log(f"[*] {len(found)} host(s) from local ARP cache.")

        if not found:
            self._log(f"[*] Ping-sweeping {prefix}.0/24...")
            for i in range(1, 255):
                ip = f"{prefix}.{i}"
                if _is_up_ping(ip):
                    found[ip] = ""

        self.scan_btn.setEnabled(True)
        self._log(f"[*] Discovery complete: {len(found)} host(s) online\n")
        for ip in sorted(found, key=lambda x: tuple(int(p) for p in x.split("."))):
            mac = found[ip] or ""
            name = ""
            try:
                name = socket.gethostbyaddr(ip)[0]
            except Exception:
                name = "unknown"
            if ip.endswith(".1") or ip == _get_local_ip():
                self._log(f"    \U0001F4A1 {ip:<16}  {mac:<26} {name}  (gateway/self)", color=GREEN)
            else:
                self._log(f"    \U0001F4A1 {ip:<16}  {mac:<26} {name}", color=CYAN)

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = NetworkMapWindow(parent)
    win.show()
    return win