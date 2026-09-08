"""Steganography Lab - The Depths

Real LSB steganography using Pillow. Hidden data is embedded in the least
significant bits of the RGB channels of a lossless PNG image, exactly the
technique used by tools like zsteg/steghide for image-based hiding.

Format: 4-byte little-endian length header + message bytes, then null-padded.
Decoding reads the length header back out, so round-trips are reliable.

Hidden messages shorter than the carrier capacity are zero-padded so decoding
does not stop on an accidental zero byte in the middle of the payload.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
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

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

HEADER_LEN = 4  # bytes of little-endian length prefix


def capacity_bits(width, height):
    """Total number of embeddable bits = pixels * channels(RGB)."""
    return width * height * 3


def embed_png(carrier_path, out_path, message):
    """Return (bytes_written, used_bits, total_bits)."""
    img = Image.open(carrier_path).convert("RGB")
    if img.format and img.format != "PNG":
        # PNG is lossless and required for reliable LSB round-trip
        img = img.convert("RGB")
    width, height = img.size
    total = capacity_bits(width, height)
    payload = message.encode("utf-8")
    need_bits = (HEADER_LEN + len(payload)) * 8
    if need_bits > total:
        raise ValueError(
            f"Message too large: {need_bits} bits needed, image holds {total} bits"
        )
    data = struct.pack("<I", len(payload)) + payload
    bits = "".join(f"{byte:08b}" for byte in data)

    pixels = list(img.getdata())
    idx = 0
    for p in range(len(pixels)):
        r, g, b = pixels[p]
        out = []
        for ch in (r, g, b):
            if idx < len(bits):
                out.append((ch & 0xFE) | int(bits[idx]))
                idx += 1
            else:
                out.append(ch)
        pixels[p] = (out[0], out[1], out[2])
    img.putdata(pixels)
    if os.path.splitext(out_path)[1].lower() != ".png":
        out_path += ".png"
    img.save(out_path, "PNG")
    return len(payload), need_bits, total


def extract_png(image_path):
    """Return the hidden message (str) or raise."""
    img = Image.open(image_path).convert("RGB")
    pixels = list(img.getdata())
    bits = []
    for r, g, b in pixels:
        bits.append(str(r & 1))
        bits.append(str(g & 1))
        bits.append(str(b & 1))
    bit_str = "".join(bits)
    # read length header
    def byte_at(offset):
        chunk = bit_str[offset:offset + 8]
        return int(chunk, 2) if len(chunk) == 8 else -1

    length = byte_at(0) | (byte_at(8) << 8) | (byte_at(16) << 16) | (byte_at(24) << 24)
    if length < 0 or length > len(pixels) * 3 // 8:
        raise ValueError("No valid length header - this image may not hold a hidden message")
    body_bits = bit_str[HEADER_LEN * 8:HEADER_LEN * 8 + length * 8]
    if len(body_bits) < length * 8:
        raise ValueError("Image too small to hold the claimed message")
    data = bytearray()
    for i in range(0, len(body_bits), 8):
        data.append(int(body_bits[i:i + 8], 2))
    return data.decode("utf-8", errors="replace")


class SteganographyWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Steganography Lab - The Depths")
        self.resize(720, 640)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")
        self._carrier_path = ""

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F3E0 Steganography Lab",
            "Hide and extract messages in images (real LSB technique)"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Mode:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.mode = QComboBox()
        self.mode.addItems(["Encode (hide message)", "Decode (extract message)"])
        self.mode.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        row.addWidget(self.mode, 1)
        layout.addLayout(row)

        self.file_row = QHBoxLayout()
        self.file_label = QLabel("No image selected")
        self.file_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        self.file_row.addWidget(self.file_label, 1)
        self.choose_btn = QPushButton("Choose image")
        self.choose_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.choose_btn.clicked.connect(self._choose)
        self.file_row.addWidget(self.choose_btn)
        layout.addLayout(self.file_row)

        self.msg_label = QLabel("Secret message:")
        self.msg_label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        layout.addWidget(self.msg_label)
        self.message = QLineEdit()
        self.message.setPlaceholderText("Your hidden message... (blank for decode)")
        self.message.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.message)
        self.mode.currentIndexChanged.connect(self._mode_changed)

        row2 = QHBoxLayout()
        self.do_btn = QPushButton("\U0001F9EA Run")
        self.do_btn.setStyleSheet(BTN_STYLE)
        self.do_btn.clicked.connect(self._run)
        row2.addWidget(self.do_btn)
        row2.addStretch()
        layout.addLayout(row2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Steganography Lab ready")
        if not HAVE_PIL:
            self._log("[!] Pillow not installed - set: pip install pillow")
        else:
            self._log("[*] Backend: Pillow (real LSB embedding)")

    def _log(self, msg):
        self.output.append(msg)

    def _mode_changed(self, idx):
        if idx == 0:
            self.msg_label.setText("Secret message:")
            self.message.setPlaceholderText("Your hidden message...")
        else:
            self.msg_label.setText("Decode (message field ignored)")
            self.message.setPlaceholderText("Hidden message extracted from chosen image")

    def _choose(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self._carrier_path = path
            self.file_label.setText(path)

    def _run(self):
        if not HAVE_PIL:
            self._log("[!] Pillow required. Install with: pip install pillow")
            return
        if not self._carrier_path:
            self._log("[!] Choose an image first")
            return
        if self.mode.currentIndex() == 0:
            msg = self.message.text()
            if not msg.strip():
                self._log("[!] Enter a message to hide")
                return
            self._encode(msg)
        else:
            self._decode()

    def _encode(self, msg):
        self.output.clear()
        out_dir = os.path.dirname(self._carrier_path) or "."
        out_path = os.path.join(out_dir, "stealth_" + os.path.basename(self._carrier_path))
        try:
            written, used, total = embed_png(self._carrier_path, out_path, msg)
        except Exception as e:
            self._log(f"[!] Encode failed: {e}")
            return
        self._log(f"[*] Carrier: {os.path.basename(self._carrier_path)}")
        self._log(f"[*] Secret: {written} bytes, used {used}/{total} embeddable bits")
        self._log(f"[*] Wrote encoded image: {out_path}")
        self.output.setTextColor(GREEN)
        self._log("[\u2714] Message hidden. The image looks identical to the naked eye.")

    def _decode(self):
        self.output.clear()
        try:
            secret = extract_png(self._carrier_path)
        except Exception as e:
            self._log(f"[!] Decode failed: {e}")
            return
        self._log(f"[*] Extracted from {os.path.basename(self._carrier_path)}")
        self.output.setTextColor(GREEN)
        self._log("[\u2714] DECODED MESSAGE:")
        self._log("")
        self._log(f"    {secret}")
        self._log("")
        self.output.setTextColor(YELLOW)
        self._log("[*] To verify: encode a message, then decode the saved image.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = SteganographyWindow(parent)
    win.show()
    return win