"""
Kraken AI — chat panel.

Streaming transcript (assistant text, tool activity, errors) plus a single
keyboard-first input line. Colors follow the Nautilus token system.
"""

import html
import time

from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class ChatPanel(QWidget):
    """Transcript + input line for talking to Kraken agents."""

    submitted = Signal(str)

    def __init__(self, colors: dict, fonts: dict, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._fonts = fonts
        self._streaming = False
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText(
            "Kraken session log…\n\nUse Agent Mode to deploy a parallel multi-agent workforce."
        )
        self._output.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background: {self._colors['deep_navy']};
                color: {self._colors['hd_white']};
                border: none;
                font-family: "{self._fonts['mono']}";
                font-size: {self._fonts['size_sm']}px;
                padding: 12px;
            }}
            """
        )
        lay.addWidget(self._output, 1)

        self._input = QLineEdit()
        self._input.setPlaceholderText("  Task…  (Enter to run, Esc to clear, Ctrl+L to clear log)")
        self._input.setClearButtonEnabled(True)
        self._input.setStyleSheet(
            f"""
            QLineEdit {{
                background: {self._colors['void_black']};
                color: {self._colors['hd_white']};
                border: 1px solid {self._colors['border']};
                padding: 8px 12px;
                font-family: "{self._fonts['mono']}";
                font-size: {self._fonts['size_md']}px;
            }}
            QLineEdit:focus {{ border: 1px solid {self._colors['seafoam']}; }}
            """
        )
        self._input.returnPressed.connect(self._on_submit)
        lay.addWidget(self._input)

    def _on_submit(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.submitted.emit(text)

    # ── Logging helpers ────────────────────────────────────────
    def _append(self, color: str, label: str, body: str, stream: bool = False):
        ts = time.strftime("%H:%M:%S")
        esc = html.escape(body).replace("\n", "<br>")
        if stream:
            cursor = self._output.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertHtml(esc)
            self._output.moveCursor(QTextCursor.End)
            return
        self._output.appendHtml(
            f"<span style='color:{self._colors['text_muted']}'>{ts}</span> "
            f"<span style='color:{color}'><b>{html.escape(label)}</b></span> "
            f"<span style='color:{self._colors['hd_white']}'>{esc}</span>"
        )

    def stream_begin(self):
        pass

    def stream_end(self):
        self._streaming = False

    def user(self, text: str):
        self._append(self._colors["seafoam"], "YOU", text)

    def assistant(self, text: str):
        if not self._streaming:
            self._append(self._colors["hd_white"], "KRAKEN", "")
            self._streaming = True
        self._append(self._colors["hd_white"], "KRAKEN", text, stream=True)

    def tool(self, text: str):
        self._append(self._colors["amber"], "TOOL", text)

    def error(self, text: str):
        self._append(self._colors["coral"], "ERROR", text)

    def status(self, text: str):
        self._append(self._colors["text_secondary"], "SYS", text)

    def memory(self, text: str):
        self._append(self._colors["emerald"], "MEM", text)

    def clear_log(self):
        self._output.clear()

    def focus_input(self):
        self._input.setFocus()
