"""RSA Playground - The Depths"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

PRIMES = [61, 53, 47, 43, 41, 37, 31, 29, 23, 19, 17, 13, 11, 7, 5, 3]


def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x, y = egcd(b, a % b)
    return (g, y, x - (a // b) * y)


def modinv(a, m):
    g, x, _ = egcd(a % m, m)
    if g != 1:
        return None
    return x % m


def rsa_encrypt(m, e, n):
    return pow(m, e, n)


def rsa_decrypt(c, d, n):
    return pow(c, d, n)


class RsaPlaygroundWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p, self.q, self.n, self.e, self.d = None, None, None, None, None
        self.setWindowTitle("RSA Playground - The Depths")
        self.resize(720, 580)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F510 RSA Playground",
            "Generate keys, encrypt, decrypt - see the math"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("p:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.p_input = QSpinBox()
        self.p_input.setRange(1, 200)
        self.p_input.setValue(61)
        self.p_input.setStyleSheet(INPUT_STYLE + "QSpinBox{padding:4px;}")
        row.addWidget(self.p_input)

        row.addWidget(QLabel("q:"))
        self.q_input = QSpinBox()
        self.q_input.setRange(1, 200)
        self.q_input.setValue(53)
        self.q_input.setStyleSheet(INPUT_STYLE + "QSpinBox{padding:4px;}")
        row.addWidget(self.q_input)

        self.gen_btn = QPushButton("\U0001F511 Generate Keys")
        self.gen_btn.setStyleSheet(BTN_STYLE)
        self.gen_btn.clicked.connect(self._generate)
        row.addWidget(self.gen_btn)
        row.addStretch()
        layout.addLayout(row)

        self.keys_label = QLabel("Keys: not generated")
        self.keys_label.setWordWrap(True)
        self.keys_label.setStyleSheet(f"color: {COLORS['gold']}; font-family: \"{FONTS['mono']}\"; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(self.keys_label)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Message (number < n):"))
        self.msg = QSpinBox()
        self.msg.setRange(0, 5000)
        self.msg.setValue(42)
        self.msg.setStyleSheet(INPUT_STYLE + "QSpinBox{padding:4px;}")
        row2.addWidget(self.msg, 1)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.enc_btn = QPushButton("\U0001F512 Encrypt")
        self.enc_btn.setStyleSheet(BTN_STYLE)
        self.enc_btn.clicked.connect(self._encrypt)
        row3.addWidget(self.enc_btn)
        self.dec_btn = QPushButton("\U0001F513 Decrypt")
        self.dec_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.dec_btn.clicked.connect(self._decrypt)
        row3.addWidget(self.dec_btn)
        row3.addStretch()
        layout.addLayout(row3)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] RSA Playground ready")
        self._log("[*] Click 'Generate Keys' to begin.")

    def _log(self, msg):
        self.output.append(msg)

    def _is_prime(self, n):
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True

    def _generate(self):
        p, q = self.p_input.value(), self.q_input.value()
        if not (self._is_prime(p) and self._is_prime(q)):
            self.output.clear()
            self.output.setTextColor(RED)
            self._log("[!] Both p and q must be prime numbers!")
            return
        if p == q:
            self.output.clear()
            self.output.setTextColor(RED)
            self._log("[!] p and q must be different primes.")
            return

        self.p, self.q = p, q
        self.n = p * q
        phi = (p - 1) * (q - 1)
        self.e = 65537
        if math.gcd(self.e, phi) != 1:
            self.e = 3
        self.d = modinv(self.e, phi)

        self.output.clear()
        self.output.setTextColor(GREEN)
        self._log("[*] Keys generated:\n")
        self._log(f"    p = {p}, q = {q}")
        self._log(f"    n (modulus) = p*q = {self.n}")
        self._log(f"    phi(n) = (p-1)(q-1) = {phi}")
        self._log(f"    e (public exp) = {self.e}")
        self._log(f"    d (private exp) = {self.d}\n")
        self.output.setTextColor(YELLOW)
        self._log(f"    PUBLIC KEY:  ({self.e}, {self.n})")
        self._log(f"    PRIVATE KEY: ({self.d}, {self.n})\n")
        self.keys_label.setText(f"Public: e={self.e}, n={self.n}   |   Private: d={self.d}, n={self.n}")

    def _encrypt(self):
        if not self.n:
            self._log("[!] Generate keys first")
            return
        m = self.msg.value()
        c = rsa_encrypt(m, self.e, self.n)
        self.output.setTextColor(GREEN)
        self._log(f"\n[*] Encrypt message {m}:")
        self._log(f"    c = m^e mod n = {m}^{self.e} mod {self.n}")
        self._log(f"    = {c}")

    def _decrypt(self):
        if not self.n:
            self._log("[!] Generate keys first")
            return
        c = self.msg.value()
        m = rsa_decrypt(c, self.d, self.n)
        self.output.setTextColor(GREEN)
        self._log(f"\n[*] Decrypt ciphertext {c}:")
        self._log(f"    m = c^d mod n = {c}^{self.d} mod {self.n}")
        self._log(f"    = {m}")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = RsaPlaygroundWindow(parent)
    win.show()
    return win
