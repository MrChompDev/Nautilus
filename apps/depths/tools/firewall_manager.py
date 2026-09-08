"""Firewall Manager - The Depths"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

SAMPLE_RULES = [
    ("ALLOW", "192.168.1.0/24", "any", "80", "Internal web"),
    ("ALLOW", "192.168.1.0/24", "any", "443", "Internal web TLS"),
    ("ALLOW", "any", "any", "22", "SSH (locked down)"),
    ("DENY",  "45.155.205.12", "any", "any", "Known attacker"),
    ("DENY",  "any", "any", "any", "Default deny all"),
]


class FirewallManagerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = [list(r) for r in SAMPLE_RULES]
        self.setWindowTitle("Firewall Manager - The Depths")
        self.resize(760, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F6E1\ufe0f Firewall Manager",
            "Build the hull - create and review firewall rules"
        ))
        layout.addWidget(hline())

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Action", "Source", "Dest", "Port", "Comment"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['bg_mid']}; color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']}; border-radius: 8px;
                font-size: {FONTS['size_sm']}px;
            }}
            QHeaderView::section {{
                background: {COLORS['bg_dark']}; color: {COLORS['text_dark']};
                border: none; padding: 6px; font-weight: bold;
            }}
        """)
        layout.addWidget(self.table, 1)

        self._reload()

        row = QHBoxLayout()
        lbl = QLabel("Action:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_sm']}px;")
        row.addWidget(lbl)
        self.action = QComboBox()
        self.action.addItems(["ALLOW", "DENY"])
        self.action.setStyleSheet(INPUT_STYLE + "QComboBox{padding:3px 8px;}")
        row.addWidget(self.action)

        row.addWidget(QLabel("Src:"))
        self.src = QLineEdit("any")
        self.src.setStyleSheet(INPUT_STYLE)
        self.src.setFixedWidth(120)
        row.addWidget(self.src)

        row.addWidget(QLabel("Dst:"))
        self.dst = QLineEdit("any")
        self.dst.setStyleSheet(INPUT_STYLE)
        self.dst.setFixedWidth(120)
        row.addWidget(self.dst)

        row.addWidget(QLabel("Port:"))
        self.port = QLineEdit("443")
        self.port.setStyleSheet(INPUT_STYLE)
        self.port.setFixedWidth(60)
        row.addWidget(self.port)

        row.addWidget(QLabel("Note:"))
        self.note = QLineEdit()
        self.note.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.note, 1)

        self.add_btn = QPushButton("+ Add Rule")
        self.add_btn.setStyleSheet(BTN_STYLE)
        self.add_btn.clicked.connect(self._add)
        row.addWidget(self.add_btn)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        self.del_btn = QPushButton("Del selected")
        self.del_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["alert_red"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.del_btn.clicked.connect(self._delete)
        row2.addWidget(self.del_btn)
        row2.addStretch()

        self.test_ip = QLineEdit("192.168.1.50")
        self.test_ip.setStyleSheet(INPUT_STYLE)
        self.test_ip.setFixedWidth(120)
        row2.addWidget(self.test_ip)
        self.test_port = QLineEdit("443")
        self.test_port.setStyleSheet(INPUT_STYLE)
        self.test_port.setFixedWidth(60)
        row2.addWidget(self.test_port)
        self.test_btn = QPushButton("Test Traffic")
        self.test_btn.setStyleSheet(BTN_STYLE)
        self.test_btn.clicked.connect(self._test)
        row2.addWidget(self.test_btn)
        layout.addLayout(row2)

        self.result = QLabel("")
        self.result.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(self.result)

    def _reload(self):
        self.table.setRowCount(len(self.rules))
        for i, r in enumerate(self.rules):
            for j, val in enumerate(r):
                item = QTableWidgetItem(str(val))
                if r[0] == "DENY":
                    item.setForeground(QColor(RED))
                else:
                    item.setForeground(QColor(GREEN))
                self.table.setItem(i, j, item)

    def _add(self):
        action = self.action.currentText()
        src = self.src.text().strip() or "any"
        dst = self.dst.text().strip() or "any"
        port = self.port.text().strip() or "any"
        note = self.note.text().strip() or "-"
        self.rules.append([action, src, dst, port, note])
        self._reload()
        self.result.setText(f"Added {action} rule: {src} -> {dst}:{port}")

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        del self.rules[row]
        self._reload()

    def _test(self):
        ip = self.test_ip.text().strip()
        port = self.test_port.text().strip()
        for action, src, dst, prt, note in self.rules:
            src_match = src in ("any", ip) or ip.startswith(src.replace("0/24",""))
            port_match = prt in ("any", port)
            if src_match and port_match:
                if action == "DENY":
                    self.result.setStyleSheet(f"color: {RED}; font-size: {FONTS['size_md']}px; font-weight: bold;")
                    self.result.setText(f"\u274C BLOCKED: {ip}:{port} denied by rule '{note}'")
                    return
                else:
                    self.result.setStyleSheet(f"color: {GREEN}; font-size: {FONTS['size_md']}px; font-weight: bold;")
                    self.result.setText(f"\u2714 ALLOWED: {ip}:{port} permitted by rule '{note}'")
                    return
        self.result.setStyleSheet(f"color: {YELLOW}; font-size: {FONTS['size_md']}px;")
        self.result.setText("\u26A0 No matching rule -> default deny. Traffic blocked.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = FirewallManagerWindow(parent)
    win.show()
    return win
