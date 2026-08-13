import os
import sys

from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from apps.Abyssal.src.ui.styles import AbyssalTheme


class AbyssalTerminal(QPlainTextEdit):
    command_executed = Signal(str)

    def __init__(self):
        super().__init__()
        self.process = None
        self.current_command = []
        self.history = []
        self.history_index = -1
        self._prompt_text = ""

        self.setup_terminal()
        self.append_prompt()
        self._start_shell()

    def setup_terminal(self):
        font = QFont("JetBrains Mono", 9)
        self.setFont(font)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {AbyssalTheme.BG_DARK};
                color: {AbyssalTheme.ACCENT};
                border: none;
                padding: 4px 8px;
            }}
        """)

    def _start_shell(self):
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._on_process_finished)

        if sys.platform == "win32":
            self.process.start("cmd.exe")
        else:
            shell = os.environ.get("SHELL", "/bin/bash")
            self.process.start(shell)

        if self.process.waitForStarted(3000):
            self.appendPlainText("Abyssal Terminal v1.0 \u2014 Shell initialized\n")
            self.append_prompt()
        else:
            self.appendPlainText("Failed to start shell.\n")

    def append_prompt(self):
        self._prompt_text = "[abyssal@chomp ~]$ "
        self.setReadOnly(False)
        self.appendPlainText(self._prompt_text)
        self.setReadOnly(True)
        self.moveCursor(QTextCursor.End)
        self.current_command = []

    def keyPressEvent(self, event):
        if self.isReadOnly():
            return

        key = event.key()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            command = "".join(self.current_command).strip()
            self.moveCursor(QTextCursor.End)
            super().keyPressEvent(event)

            if command:
                self.history.append(command)
                self.history_index = len(self.history)
                self._execute(command)
            else:
                self.append_prompt()
            return

        if key == Qt.Key_Backspace:
            if self.current_command:
                self.current_command.pop()
                super().keyPressEvent(event)
            return

        if key == Qt.Key_Up:
            if self.history_index > 0:
                self.history_index -= 1
                self._replace_input(self.history[self.history_index])
            return

        if key == Qt.Key_Down:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self._replace_input(self.history[self.history_index])
            else:
                self.history_index = len(self.history)
                self._replace_input("")
            return

        if key == Qt.Key_Left:
            super().keyPressEvent(event)
            return

        if key == Qt.Key_Right:
            super().keyPressEvent(event)
            return

        if key == Qt.Key_Home:
            super().keyPressEvent(event)
            return

        if key == Qt.Key_End:
            super().keyPressEvent(event)
            return

        if event.text():
            self.current_command.append(event.text())
            self.setReadOnly(False)
            super().keyPressEvent(event)
            self.setReadOnly(True)

    def _replace_input(self, new_text):
        text = self.toPlainText()
        last_prompt = text.rfind(self._prompt_text) + len(self._prompt_text)
        self.setReadOnly(False)
        self.setPlainText(text[:last_prompt] + new_text)
        self.setReadOnly(True)
        self.moveCursor(QTextCursor.End)
        self.current_command = list(new_text)

    def _execute(self, command):
        if command.lower() in ("clear", "cls"):
            self.clear()
            self.append_prompt()
            return

        if self.process and self.process.state() == QProcess.Running:
            self.process.write((command + "\n").encode("utf-8"))
            self.command_executed.emit(command)
        else:
            self._start_shell()
            if self.process and self.process.state() == QProcess.Running:
                self.process.write((command + "\n").encode("utf-8"))

    def _read_output(self):
        if not self.process:
            return
        output = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.setReadOnly(False)
        self.appendPlainText(output.rstrip())
        self.setReadOnly(True)
        self.append_prompt()

    def _on_process_finished(self):
        self.appendPlainText("\n[Process finished]\n")
        self.append_prompt()

    def execute_command(self, command):
        self.show()
        self.setFocus()
        self.setReadOnly(False)
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(command)
        self.setReadOnly(True)
        self.current_command = list(command)
        self._execute("\r")

    def cleanup(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.process.waitForFinished(1000)
