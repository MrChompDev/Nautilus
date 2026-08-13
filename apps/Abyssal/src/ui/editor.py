from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QTextCursor,
    QTextDocument,
    QTextFormat,
)
from PySide6.QtWidgets import QFileDialog, QPlainTextEdit, QTextEdit, QWidget

from apps.Abyssal.src.engines.highlighter import AbyssalHighlighter, detect_language
from apps.Abyssal.src.ui.styles import AbyssalTheme


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class AbyssalEditor(QPlainTextEdit):
    cursor_moved = Signal(int, int)
    language_changed = Signal(str)
    modification_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.file_path = None
        self.language = "text"
        self._modified = False

        self.setup_editor()
        self.highlighter = AbyssalHighlighter(self.document())
        self.line_number_area = LineNumberArea(self)
        self.update_line_number_area_width(0)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self._emit_cursor_pos)
        self.textChanged.connect(self._on_text_changed)
        self.highlight_current_line()

    def setup_editor(self):
        font = QFont("JetBrains Mono", 10)
        self.setFont(font)
        self.setTabStopDistance(font.pointSizeF() * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setCenterOnScroll(True)
        self.setMouseTracking(True)

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: none;
                padding-left: 4px;
                selection-background-color: {AbyssalTheme.SELECTION};
                selection-color: {AbyssalTheme.TEXT};
            }}
            QPlainTextEdit::item {{
                padding: 0;
                margin: 0;
            }}
        """)

    # ── Line Numbers ────────────────────────────────────

    def line_number_area_width(self):
        digits = max(1, len(str(max(1, self.blockCount()))))
        space = 10 + self.fontMetrics().horizontalAdvance("9") * digits + 16
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(AbyssalTheme.PANEL_ALT))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                is_current = block_number == current_line

                if is_current:
                    painter.setPen(QColor(AbyssalTheme.LINE_NUM_CURRENT))
                    painter.fillRect(0, top, self.line_number_area.width(),
                                     round(self.blockBoundingRect(block).height()),
                                     QColor(AbyssalTheme.LINE_HIGHLIGHT))
                else:
                    painter.setPen(QColor(AbyssalTheme.LINE_NUM))

                painter.drawText(
                    0, top, self.line_number_area.width() - 8,
                    self.fontMetrics().height(), Qt.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
        painter.end()

    # ── Active Line Highlight ───────────────────────────

    def highlight_current_line(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(AbyssalTheme.LINE_HIGHLIGHT))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    # ── Bracket Matching ────────────────────────────────

    def _match_brackets(self):
        cursor = self.textCursor()
        pos = cursor.position()
        doc = self.document()

        char_before = doc.toPlainText()[pos - 1:pos] if pos > 0 else ""
        char_after = doc.toPlainText()[pos:pos + 1] if pos < doc.characterCount() else ""

        brackets = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{"}

        check_char = None
        direction = None

        if char_before in brackets:
            check_char = char_before
            direction = 1
        elif char_after in brackets:
            check_char = char_after
            direction = -1

        if check_char:
            target = brackets[check_char]
            count = 1
            search_pos = pos + direction

            while 0 <= search_pos < doc.characterCount() and count > 0:
                c = doc.toPlainText()[search_pos:search_pos + 1]
                if c == check_char:
                    count += 1
                elif c == target:
                    count -= 1
                search_pos += direction

            if count == 0:
                match_pos = search_pos - direction
                return pos - 1, match_pos

        return None

    # ── File Operations ─────────────────────────────────

    def open_file(self, file_path):
        try:
            with open(file_path, encoding="utf-8") as f:
                self.setPlainText(f.read())
            self.file_path = file_path
            self.set_language(detect_language(file_path))
            self.document().setModified(False)
            self._modified = False
            self.modification_changed.emit(False)
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="latin-1") as f:
                    self.setPlainText(f.read())
                self.file_path = file_path
                self.set_language(detect_language(file_path))
                self.document().setModified(False)
                self._modified = False
            except Exception as e:
                print(f"Error opening file: {e}")
        except Exception as e:
            print(f"Error opening file: {e}")

    def save_file(self):
        if self.file_path:
            try:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write(self.toPlainText())
                self.document().setModified(False)
                self._modified = False
                self.modification_changed.emit(False)
                return True
            except Exception as e:
                print(f"Error saving file: {e}")
                return False
        else:
            return self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "",
            "All Files (*);;Python (*.py);;JavaScript (*.js);;C/C++ (*.c *.cpp);;HTML (*.html);;CSS (*.css)"
        )
        if file_path:
            self.file_path = file_path
            self.set_language(detect_language(file_path))
            return self.save_file()
        return False

    def set_language(self, lang):
        self.language = lang
        self.highlighter.set_language(lang)
        self.language_changed.emit(lang)

    # ── Internal ────────────────────────────────────────

    def _on_text_changed(self):
        mod = self.document().isModified()
        if mod != self._modified:
            self._modified = mod
            self.modification_changed.emit(mod)

    def _emit_cursor_pos(self):
        cursor = self.textCursor()
        self.cursor_moved.emit(cursor.blockNumber() + 1, cursor.columnNumber() + 1)

    def get_cursor_pos(self):
        cursor = self.textCursor()
        return {"block": cursor.blockNumber(), "column": cursor.columnNumber()}

    def set_cursor_pos(self, pos):
        cursor = self.textCursor()
        block = self.document().findBlockByLineNumber(pos["block"])
        cursor.setPosition(block.position() + pos["column"])
        self.setTextCursor(cursor)

    # ── Find / Replace ──────────────────────────────────

    def find_text(self, text, case_sensitive=False, whole_word=False, regex=False):
        if not text:
            return False

        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords

        if regex:
            found = self.find(text, flags)
        else:
            found = self.find(text, flags)

        return found

    def find_next(self, text, case_sensitive=False, whole_word=False, regex=False):
        if not text:
            return False
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords
        return self.find(text, flags)

    def find_prev(self, text, case_sensitive=False, whole_word=False, regex=False):
        if not text:
            return False
        flags = QTextDocument.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords
        return self.find(text, flags)

    def replace_current(self, replacement):
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.insertText(replacement)

    def replace_all(self, text, replacement, case_sensitive=False, whole_word=False, regex=False):
        if not text:
            return 0

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.setTextCursor(cursor)

        count = 0
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords

        while self.find(text, flags):
            self.textCursor().insertText(replacement)
            count += 1

        return count

    def _line_text(self):
        return self.textCursor().block().text()
