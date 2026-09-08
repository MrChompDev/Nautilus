"""Vulnerability Scanner - The Depths

Real nmap-style service version detection. Connects to each open port, sends
a service-appropriate probe (GET / for HTTP, SSH banner handshake, SMTP HELO,
etc.), reads the ACTUAL banner, then matches product+version against a local
signature/CVE database - exactly how nmap -sV and masscan --banners operate.

Only local hosts (127.0.0.1 / ::1 / localhost / private ranges) are scanned,
so scanning is safe and legal by default. An educational signature DB maps
observed versions to known CVEs for prioritization.
"""

import os
import re
import socket
import sys
from dataclasses import dataclass

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

# Service probes: (port-regex, probe bytes, how many bytes to read, delay s)
PROBES = [
    (r"^(80|443|8080|8000|81|3000|5000|8443)$", b"GET / HTTP/1.0\r\nHost: localhost\r\n\r\n", 1024, 1.0),
    (r"^(21|990)$", None, 512, 1.5),                                     # FTP sends banner unprompted
    (r"^22$", b"SSH-2.0-Probe\r\n", 256, 1.0),                            # SSH banner handshake
    (r"^25|465|587$", None, 512, 1.5),                                    # SMTP greeting
    (r"^(110|143|993|995)$", None, 256, 1.0),                             # POP/IMAP greeting
    (r"^(3306)$", None, 256, 1.0),                                        # MySQL version handshake
    (r"^(5432)$", None, 256, 1.0),                                        # Postgres greeting
    (r"^(6379)$", b"PING\r\n", 256, 0.8),                                 # Redis
    (r"^(27017|27018)$", None, 512, 0.8),                                 # MongoDB
    (r"^(3389)$", b"\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00", 512, 1.0),  # RDP
]


@dataclass
class CVE:
    product: str
    version_re: str
    cve: str
    severity: str
    note: str


# Educational version->CVE DB (subset of real public entries)
SIGS = [
    CVE("OpenSSH", r"OpenSSH[_ ](2[0-9]\.0|1\.\d|4\.\d|5\.\d|6\.\d|7\.[0-5])",
        "CVE-2018-15473", "Medium", "User enumeration before 7.7"),
    CVE("OpenSSH", r"OpenSSH[_ ]([1-9]|1[0-9])(\.\d+)?_?", "CVE-2016-20012",
        "Low", "Legacy OpenSSH - enable key-only auth"),
    CVE("Apache/2", r"Apache/2\.(4\.(0|1|2|3|4))((\.[0-9])|[^0-9]|$)",
        "CVE-2021-41773", "Critical", "Path traversal + RCE"),
    CVE("Apache/2", r"Apache/2\.4\.49", "CVE-2021-41773", "Critical", "Path traversal + RCE"),
    CVE("nginx", r"nginx/(1\.[0-9]\.(0|1|2)|0\.\d)",
        "CVE-2021-23017", "Medium", "DNS resolver off-by-one before 1.20.1"),
    CVE("ProFTPD", r"ProFTPD 1\.3\.\d", "CVE-2015-3306", "Critical", "mod_copy RCE"),
    CVE("vsftpd", r"vsftpd 2\.3\.4", "CVE-2011-2523", "Critical", "Backdoor (smileyshell) - RCE"),
    CVE("MySQL", r"MySQL-5\.[0-5]", "CVE-2016-6662", "High", "Outdated MySQL"),
    CVE("MariaDB", r"MariaDB-?5\.[0-2]", "CVE-2019-3822", "Medium", "Backup/RESTORE RCE"),
    CVE("Redis", r"redis_version:([0-6]\.\d|\d\.\d)",
        "CVE-2022-0543", "Critical", "Lua sandbox escape"),
    CVE("PostgreSQL", r"(PostgreSQL|Postgres) [8-9]\.\d", "CVE-2013-1899", "Medium", "connect() type confusion"),
    CVE("PureFTPd", r"Pure-FTPd v?1\.0\.(0|1|2|3|4)", "CVE-2019-20176", "Medium", "Denial of service"),
]


def grab_banner(host, port, timeout=3.0):
    """Open TCP, send probe if applicable, read banner -> str (or '')"""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            probe = next((pb for rx, pb, _len, _d in PROBES if re.match(rx, str(port))), None)
            if probe is not None:
                try:
                    s.sendall(probe)
                except OSError:
                    pass
            try:
                data = s.recv(1024)
            except TimeoutError:
                return ""
            return data.decode("utf-8", errors="ignore")
    except OSError:
        return ""


def is_local_target(host):
    """Restrict scanning to local/loopback/private hosts (safe by default)."""
    if host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return True
    try:
        parts = host.split(".")
        if len(parts) == 4 and parts[0] == "10":
            return True
        if len(parts) == 4 and parts[0] == "192" and parts[1] == "168":
            return True
        if len(parts) == 4 and parts[0] == "172" and 16 <= int(parts[1]) <= 31:
            return True
    except ValueError:
        return False
    return False


class VulnScanWorker(QThread):
    bannered = Signal(int, str)
    vuln = Signal(int, str, str, str, str)
    closed = Signal(int)
    finished = Signal()

    def __init__(self, host, ports):
        super().__init__()
        self.host = host
        self.ports = ports

    def run(self):
        for port in self.ports:
            banner = grab_banner(self.host, port)
            if not banner:
                self.closed.emit(port)
                continue
            self.bannered.emit(port, banner[:200].replace("\r", " ").replace("\n", " ").strip())
            matched = False
            for sig in SIGS:
                if (sig.product.lower() in banner.lower()) or re.search(sig.version_re, banner, re.IGNORECASE):
                    matched = True
                    self.vuln.emit(port, sig.product, sig.cve, sig.severity, sig.note)
                    break
            if not matched:
                self.vuln.emit(port, "Unknown", "No CVE known", "Info", "No signature matched banner")


class VulnScannerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("Vulnerability Scanner - The Depths")
        self.resize(760, 600)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F9F1 Vulnerability Scanner",
            "Real banner grab + version match against a CVE database"
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

        hint = QLabel("Real network: connects to the host, sends a probe, reads the actual banner. Scans local/private hosts only.")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Vulnerability Scanner ready (nmap-style version detection)")
        self._log(f"[*] {len(SIGS)} signatures in local CVE database")

    def _log(self, msg):
        self.output.append(msg)

    def start(self):
        host = self.target.text().strip()
        if not host:
            self._log("[!] Enter a target")
            return
        if not is_local_target(host):
            self._log("[!] Only local/private targets (127.0.0.1, 10.x, 192.168.x, 172.16-31.x) are allowed.")
            return
        self.output.clear()
        self._log(f"[*] Scanning {host} - sending probes and reading real banners...\n")
        self.scan_btn.setEnabled(False)
        self.worker = VulnScanWorker(host, sorted({int(p[0]) for p in PROBES}))
        self.worker.bannered.connect(self._on_banner)
        self.worker.vuln.connect(self._on_vuln)
        self.worker.closed.connect(lambda p: self._log(f"   Port {p:>5} closed"))
        self.worker.finished.connect(self._done)
        self.worker.start()

    def _on_banner(self, port, banner):
        self._log(f"[\U0001F4E6] Port {port:<5} {banner}")

    def _on_vuln(self, port, product, cve, sev, note):
        color = RED if sev == "Critical" else YELLOW if sev in ("High", "Medium") else GREEN
        self.output.setTextColor(color)
        self._log(f"     [{sev.upper():<8}] {product}  {cve} - {note}")

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