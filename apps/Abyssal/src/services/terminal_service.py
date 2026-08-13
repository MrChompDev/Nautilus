import os
import sys

from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPlainTextEdit

from apps.Abyssal.src.core.event_bus import emit


class TerminalService:
    def __init__(self) -> None:
        self._process: QProcess = None
        self._output_buffer: str = ""

    def create_terminal_widget(self, parent=None) -> 'TerminalWidget':
        widget = TerminalWidget(parent)
        widget.command_executed.connect(self._on_command_executed)
        return widget

    def _on_command_executed(self, command: str) -> None:
        emit("terminal.command", command)


class TerminalWidget(QPlainTextEdit):
    command_executed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._current_command = []
        self._history = []
        self._history_index = -1
        self._prompt_text = ""

        self._setup_terminal()
        self._append_prompt()
        self._start_shell()

    def _setup_terminal(self):
        font = QFont("JetBrains Mono", 9)
        self.setFont(font)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #060F1A;
                color: #00F2C2;
                border: none;
                padding: 4px 8px;
                selection-background-color: #00F2C2;
                selection-color: #081626;
            }
        """)

    def _start_shell(self):
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.finished.connect(self._on_process_finished)

        if sys.platform == "win32":
            self._process.start("cmd.exe")
        else:
            shell = os.environ.get("SHELL", "/bin/bash")
            self._process.start(shell)

        if self._process.waitForStarted(3000):
            self.appendPlainText("Abyssal Terminal v2.0 \u2014 Shell initialized")
            self._append_prompt()
        else:
            self.appendPlainText("Failed to start shell")

    def _append_prompt(self):
        self._prompt_text = "[abyssal@chomp ~]$ "
        self.setReadOnly(False)
        self.appendPlainText(self._prompt_text)
        self.setReadOnly(True)
        self.moveCursor(self.textCursor().MoveOperation.End)
        self._current_command = []

    def keyPressEvent(self, event):
        if self.isReadOnly():
            return

        key = event.key()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            command = "".join(self._current_command).strip()
            self.moveCursor(self.textCursor().MoveOperation.End)
            super().keyPressEvent(event)

            if command:
                self._history.append(command)
                self._history_index = len(self._history)
                self._execute(command)
            else:
                self._append_prompt()
            return

        if key == Qt.Key_Backspace:
            if self._current_command:
                self._current_command.pop()
                super().keyPressEvent(event)
            return

        if key == Qt.Key_Up:
            if self._history_index > 0:
                self._history_index -= 1
                self._replace_input(self._history[self._history_index])
            return

        if key == Qt.Key_Down:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self._replace_input(self._history[self._history_index])
            else:
                self._history_index = len(self._history)
                self._replace_input("")
            return

        if event.text():
            self._current_command.append(event.text())
            self.setReadOnly(False)
            super().keyPressEvent(event)
            self.setReadOnly(True)

    def _replace_input(self, new_text: str) -> None:
        text = self.toPlainText()
        last_prompt = text.rfind(self._prompt_text) + len(self._prompt_text)
        self.setReadOnly(False)
        self.setPlainText(text[:last_prompt] + new_text)
        self.setReadOnly(True)
        self.moveCursor(self.textCursor().MoveOperation.End)
        self._current_command = list(new_text)

    def _execute(self, command: str) -> None:
        if command.lower() in ("clear", "cls"):
            self.clear()
            self._append_prompt()
            return

        if self._process and self._process.state() == QProcess.Running:
            self._process.write((command + "\n").encode("utf-8"))
            self.command_executed.emit(command)
        else:
            self._start_shell()
            if self._process and self._process.state() == QProcess.Running:
                self._process.write((command + "\n").encode("utf-8"))

    def _read_output(self) -> None:
        if not self._process:
            return
        output = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.setReadOnly(False)
        self.appendPlainText(output.rstrip())
        self.setReadOnly(True)
        self._append_prompt()

    def _on_process_finished(self) -> None:
        self.appendPlainText("\n[Process finished]")
        self._append_prompt()

    def execute_command(self, command: str) -> None:
        self.show()
        self.setFocus()
        self.setReadOnly(False)
        self.moveCursor(self.textCursor().MoveOperation.End)
        self.insertPlainText(command)
        self.setReadOnly(True)
        self._current_command = list(command)
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
        self.keyPressEvent(event)

    def cleanup(self) -> None:
        if self._process and self._process.state() == QProcess.Running:
            self._process.kill()
            self._process.waitForFinished(1000)