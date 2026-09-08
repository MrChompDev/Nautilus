"""Port Scanner - The Depths"""

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
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, INPUT_STYLE, OUT_STYLE, hline, make_header
from core.theme import COLORS, FONTS

COMMON_PORTS = {
    20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 111: "RPC", 135: "MS-RPC",
    139: "NetBIOS", 143: "IMAP", 161: "SNMP", 443: "HTTPS", 445: "SMB",
    465: "SMTPS", 587: "SMTP-Sub", 993: "IMAPS", 995: "POP3S",
    1080: "SOCKS", 1433: "MSSQL", 1521: "Oracle", 3306: "MySQL",
    3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
}


class ScanWorker(QThread):
    port_open = Signal(int, str)
    progress = Signal(int)
    finished = Signal()
    log = Signal(str)

    def __init__(self, host, start, end, timeout=1.0):
        super().__init__()
        self.host = host
        self.start = start
        self.end = end
        self.timeout = timeout
        self._running = True

    def run(self):
        ports = list(range(self.start, self.end + 1))
        total = len(ports)
        for i, port in enumerate(ports):
            if not self._running:
                break
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.timeout)
                    result = s.connect_ex((self.host, port))
                    if result == 0:
                        service = COMMON_PORTS.get(port, "unknown")
                        self.port_open.emit(port, service)
            except socket.gaierror:
                self.log.emit(f"[!] DNS resolution failed for {self.host}")
                break
            except OSError:
                pass
            self.progress.emit(int((i + 1) / total * 100))
        self.finished.emit()

    def stop(self):
        self._running = False


class PortScannerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.open_ports = []
        self.setWindowTitle("Port Scanner - The Depths")
        self.resize(620, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F9ED Port Scanner",
            "Directory of Open Doors - scan a target for listening services"
        ))
        layout.addWidget(hline())

        # Target input
        row = QHBoxLayout()
        lbl = QLabel("Target:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)

        self.target = QLineEdit("127.0.0.1")
        self.target.setPlaceholderText("IP or hostname")
        self.target.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.target, 1)

        self.range_start = QSpinBox()
        self.range_start.setRange(1, 65535)
        self.range_start.setValue(1)
        self.range_start.setStyleSheet(INPUT_STYLE + "QSpinBox { padding: 4px; }")
        row.addWidget(QLabel("from:"))
        row.addWidget(self.range_start)

        self.range_end = QSpinBox()
        self.range_end.setRange(1, 65535)
        self.range_end.setValue(1024)
        self.range_end.setStyleSheet(INPUT_STYLE + "QSpinBox { padding: 4px; }")
        row.addWidget(QLabel("to:"))
        row.addWidget(self.range_end)
        layout.addLayout(row)

        # Controls
        ctrl = QHBoxLayout()
        self.scan_btn = QPushButton("\U0001F50D Start Scan")
        self.scan_btn.setStyleSheet(BTN_STYLE)
        self.scan_btn.clicked.connect(self.start_scan)
        ctrl.addWidget(self.scan_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(BTN_STYLE.replace(COLORS['teal'], COLORS['alert_red']).replace(COLORS['teal_light'], COLORS['coral_deep']))
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        ctrl.addWidget(self.stop_btn)

        self.status = QLabel("Ready")
        self.status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        ctrl.addWidget(self.status)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background: {COLORS['bg_mid']}; border: 1px solid {COLORS['border']};
                border-radius: 4px; height: 10px; text-align: center; }}
            QProgressBar::chunk {{ background: {COLORS['teal']}; border-radius: 4px; }}
        """)
        layout.addWidget(self.progress)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Port Scanner initialized")
        self._log("[*] Try scanning 127.0.0.1 ports 1-1024 (your own machine)")

    def _log(self, msg):
        self.output.append(msg)

    def start_scan(self):
        host = self.target.text().strip()
        if not host:
            self._log("[!] Enter a target host")
            return
        start = self.range_start.value()
        end = self.range_end.value()
        self.open_ports = []
        self.output.clear()
        self._log(f"[*] Scanning {host} ports {start}-{end}")
        self._log("[*] Technique: TCP Connect Scan\n")
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status.setText("Scanning...")

        self.worker = ScanWorker(host, start, end)
        self.worker.port_open.connect(self._on_port)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self._scan_done)
        self.worker.log.connect(self._log)
        self.worker.start()

    def stop_scan(self):
        if self.worker:
            self.worker.stop()
            self._log("\n[*] Scan stopped by user")

    def _on_port(self, port, service):
        self.open_ports.append((port, service))
        self._log(f"    \u2714 Port {port:<6} open   ({service})")

    def _scan_done(self):
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setValue(100)
        self.status.setText(f"Done - {len(self.open_ports)} open")
        self._log(f"\n[*] Scan complete: {len(self.open_ports)} open ports found")
        if not self.open_ports:
            self._log("[*] No open ports in the scanned range.")

    def closeEvent(self, event):
        self.stop_scan()
        super().closeEvent(event)


def run(parent=None):
    win = PortScannerWindow(parent)
    win.show()
    return win
