"""
Abyssal — Kraken AI chat panel.

Toggleable right-hand panel that streams answers from the local Nautilus
"coding" model, scoped to the folder of the currently open file via the
project brain. Runs inference off the UI thread so typing stays smooth.
"""

import html
import time

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from apps.Abyssal.src.ui.styles import AbyssalTheme


class _KrakenWorker(QThread):
    """Drives ChatClient.stream() off-thread; emits deltas via signals."""

    chunk = Signal(str)
    done = Signal()
    failed = Signal(str)
    status = Signal(str)

    def __init__(self, model, workspace, messages, parent=None):
        super().__init__(parent)
        self._model = model
        self._workspace = workspace
        self._messages = messages

    def run(self):
        from apps.kraken.engine.providers import ChatClient

        client = ChatClient(
            provider="nautilus",
            model=self._model,
            workspace=self._workspace,
            temperature=0.5,
            max_tokens=256,
            on_chunk=lambda t: self.chunk.emit(t),
            on_status=lambda s: self.status.emit(s),
        )
        try:
            for _ in client.stream(self._messages):
                pass
            self.done.emit()
        except Exception as e:  # noqa: BLE001 — surface any backend failure in the UI
            self.failed.emit(str(e))


class KrakenChatPanel(QWidget):
    """Transcript + input wired to the local Nautilus coding model."""

    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._history: list[dict] = []
        self._workspace = None
        self._model = "coding"
        self._build_ui()
        self.setMinimumWidth(300)

    def _build_ui(self):
        t = AbyssalTheme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(12, 8, 8, 8)
        self._title = QLabel("Kraken · coding")
        self._title.setStyleSheet(f"color: {t.TEXT}; font-weight: bold;")
        header.addWidget(self._title)
        header.addStretch(1)
        self._status = QLabel("local")
        self._status.setStyleSheet(f"color: {t.TEXT_MUTED};")
        header.addWidget(self._status)
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setToolTip("Clear transcript")
        self._clear_btn.clicked.connect(self.clear_log)
        header.addWidget(self._clear_btn)
        close_btn = QPushButton()
        close_btn.setToolTip("Close chat (Ctrl+Shift+C)")
        close_btn.setFixedSize(26, 24)
        from core.controls import control_icon

        close_btn.setIcon(control_icon("close"))
        close_btn.setIconSize(close_btn.iconSize() * 0.7)
        close_btn.clicked.connect(self.close_requested)
        header.addWidget(close_btn)
        lay.addLayout(header)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText(
            "Kraken coding assistant — reads your project via the brain.\n"
            "Ask about code, get suggestions, or have it draft edits."
        )
        self._output.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background: {t.BG_DARK};
                color: {t.TEXT};
                border: none;
                border-top: 1px solid {t.BORDER};
                padding: 8px;
            }}
            """
        )
        lay.addWidget(self._output, 1)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(8, 8, 8, 8)
        input_row.setSpacing(6)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask Kraken about this project…  (Ctrl+Shift+C to toggle)")
        self._input.returnPressed.connect(self._on_submit)
        input_row.addWidget(self._input, 1)
        self._send_btn = QPushButton()
        from core.controls import control_icon

        self._send_btn.setIcon(control_icon("send"))
        self._send_btn.setIconSize(self._send_btn.iconSize() * 0.7)
        self._send_btn.setFixedWidth(56)
        self._send_btn.setToolTip("Send (Enter)")
        self._send_btn.clicked.connect(self._on_submit)
        input_row.addWidget(self._send_btn)
        lay.addLayout(input_row)

    # ── State ───────────────────────────────────────────────────
    def set_workspace(self, path):
        self._workspace = path
        if path:
            name = path.rstrip("/").split("/")[-1] or path
            self._title.setText(f"Kraken · coding · {name}")

    def workspace(self):
        return self._workspace

    def clear_log(self):
        self._output.clear()

    def focus_input(self):
        self._input.setFocus()

    # ── Conversation flow ───────────────────────────────────────
    def _append(self, color: str, label: str, body: str, stream: bool = False):
        esc = html.escape(body).replace("\n", "<br>")
        if stream:
            cursor = self._output.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertHtml(esc)
            self._output.moveCursor(QTextCursor.End)
            return
        ts = time.strftime("%H:%M:%S")
        self._output.appendHtml(
            f"<span style='color:{AbyssalTheme.TEXT_MUTED}'>{ts}</span> "
            f"<span style='color:{color}'><b>{html.escape(label)}</b></span> "
            f"<span style='color:{AbyssalTheme.TEXT}'>{esc}</span>"
        )

    def _on_submit(self):
        text = self._input.text().strip()
        if not text:
            return
        if self._worker is not None and self._worker.isRunning():
            self._status.setText("busy…")
            return
        self._input.clear()
        self._append(AbyssalTheme.ACCENT, "YOU", text)
        self._history.append({"role": "user", "content": text})
        if len(self._history) > 12:
            self._history = self._history[-12:]
        self._start_stream()

    def _start_stream(self):
        try:
            from apps.kraken.engine.local import list_local_models
        except Exception:  # noqa: BLE001
            self._append(AbyssalTheme.CORAL, "ERROR", "Kraken runtime not available")
            return
        available = {m["id"] for m in list_local_models()}
        model = next((m for m in ("coding", "writing", "pentest") if m in available), self._model)
        self._title.setText(f"Kraken · {model}")
        self._append(AbyssalTheme.TEXT_DIM, "KRAKEN", "")
        self._worker = _KrakenWorker(model, self._workspace, list(self._history), self)
        self._worker.chunk.connect(self._on_chunk)
        self._worker.status.connect(self._on_status)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._status.setText("thinking…")
        self._worker.start()

    def _on_chunk(self, text: str):
        if text and text != "\x00":
            self._append(AbyssalTheme.TEXT, "", text, stream=True)

    def _on_status(self, text: str):
        self._status.setText(text)

    def _on_done(self):
        self._status.setText("local")
        self._output.moveCursor(QTextCursor.End)

    def _on_failed(self, message: str):
        self._status.setText("local")
        self._append(AbyssalTheme.CORAL, "ERROR", message)

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(500)
        super().closeEvent(event)
