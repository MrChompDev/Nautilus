"""Packet Injector - The Depths (educational)"""

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

from apps.depths.tools._ui import BTN_STYLE, CYAN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS


class PacketInjectorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Packet Injector - Signal Depths (Educational)")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4E8 Packet Injector",
            "Craft custom packets - understand protocol structure"
        ))
        layout.addWidget(hline())

        warn = QLabel("\u26A0 Requires raw socket privileges (root). Educational - for tossing packets in your own lab.")
        warn.setWordWrap(True)
        warn.setStyleSheet(f"color: {COLORS['warning']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(warn)

        row = QHBoxLayout()
        lbl = QLabel("Protocol:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.proto = QComboBox()
        self.proto.addItems(["TCP SYN", "TCP ACK", "ICMP Echo", "UDP"])
        self.proto.setStyleSheet(INPUT_STYLE + "QComboBox{padding:4px 8px;}")
        row.addWidget(self.proto, 1)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Dest IP:"))
        self.dst = QLineEdit("127.0.0.1")
        self.dst.setStyleSheet(INPUT_STYLE)
        row2.addWidget(self.dst, 1)

        row2.addWidget(QLabel("Port:"))
        self.port = QLineEdit("80")
        self.port.setStyleSheet(INPUT_STYLE)
        self.port.setFixedWidth(70)
        row2.addWidget(self.port)
        layout.addLayout(row2)

        self.craft_btn = QPushButton("\U0001F6E0 Craft & Inspect")
        self.craft_btn.setStyleSheet(BTN_STYLE)
        self.craft_btn.clicked.connect(self._craft)
        layout.addWidget(self.craft_btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Packet Injector ready")

    def _log(self, msg):
        self.output.append(msg)

    def _craft(self):
        proto = self.proto.currentText()
        dst = self.dst.text().strip() or "127.0.0.1"
        port = int(self.port.text().strip() or "80")

        self.output.clear()
        self.output.setTextColor(CYAN)
        self._log(f"[*] Crafting {proto} packet to {dst}:{port}\n")

        if proto == "TCP SYN":
            src = 12345
            self._log("[*] IP Header:")
            self._log("    Version=4, IHL=5, Total Length=40")
            self._log(f"    Protocol=6 (TCP), Source=127.0.0.1, Dest={dst}")
            self._log("[*] TCP Header:")
            self._log(f"    Src Port={src}, Dst Port={port}")
            self._log("    Sequence=1337, Flags=SYN (0x02)")
            self._log("\n[*] Hex dump (crafted):")
            hexbytes = "4500 0028 0001 0000 4006 0000 7f00 0001"
            src_ip = "7f00 0001"
            tcphdr = f"{src:04x} {port:04x} 0539 0000 5002 0000 0000 0000"
            self._log(f"    {hexbytes}  {src_ip}")
            self._log(f"    {tcphdr}")
        elif proto == "TCP ACK":
            self._log("[*] ACK packet - acknowledges received data")
            self._log(f"    Src=43210, Dst={port}, Flags=ACK (0x10)")
            self._log("\n[*] TCP header (raw):")
            self._log(f"    {43210:04x} {port:04x} 0000 0000 5010 0000 0000 0000")
        elif proto == "ICMP Echo":
            self._log("[*] ICMP Echo Request (ping)")
            self._log("    Type=8, Code=0, Checksum, Identifier=1, Seq=1")
            self._log("\n[*] Crafted payload:")
            self._log("    0800 0000 0001 0001")
        else:
            self._log("[*] UDP datagram")
            self._log(f"    Src Port=50000, Dst Port={port}, Length=8+payload")
            self._log("\n[*] UDP header:")
            self._log(f"    c350 {port:04x} 000c 0000")

        self.output.setTextColor(YELLOW)
        self._log("\n[*] To actually inject, you'd open a RAW socket:")
        self._log("    socket.socket(socket.AF_INET, socket.SOCK_RAW, proto)")
        self._log("    Requires root and NIC in the right mode.")
        self._log("[*] Educational: use Scapy in a lab VM for real injection.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = PacketInjectorWindow(parent)
    win.show()
    return win
