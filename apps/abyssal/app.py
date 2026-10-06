"""Abyssal — Code Editor"""

import os

from PySide6.QtCore import QDir, QRect, QSize, Qt, QRegularExpression
from PySide6.QtGui import (
    QColor,
    QFont,
    QFileSystemModel,
    QKeySequence,
    QPainter,
    QShortcut,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextFormat,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from core.theme import COLORS, FONTS


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_area = LineNumberArea(self)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.blockCountChanged.connect(self.update_line_area_width)
        self.updateRequest.connect(self.update_line_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = max(1, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_area_width(self, _count):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_area(self, rect, dy):
        if dy:
            self.line_area.scroll(0, dy)
        else:
            self.line_area.update(0, rect.y(), self.line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def highlight_current_line(self):
        if self.isReadOnly():
            return
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor(COLORS["hover"]))
        sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self.setExtraSelections([sel])

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_area)
        painter.fillRect(event.rect(), QColor(COLORS["bg_mid"]))
        block = self.firstVisibleBlock()
        offset = self.contentOffset()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                painter.setPen(
                    QColor(COLORS["ice"] if number == current else COLORS["text_muted"])
                )
                painter.drawText(
                    0, top, self.line_area.width() - 6, self.fontMetrics().height(),
                    Qt.AlignRight | Qt.AlignVCenter, str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            line = cursor.block().text()
            indent = line[: len(line) - len(line.lstrip())]
            if line.rstrip().endswith(":"):
                indent += "    "
            super().keyPressEvent(event)
            self.insertPlainText(indent)
            return
        super().keyPressEvent(event)


class PythonHighlighter(QSyntaxHighlighter):
    STATE_NORMAL = 0
    STATE_DQ = 1
    STATE_SQ = 2

    KEYWORDS = (
        "and as assert async await break class continue def del elif else except "
        "finally for from global if import in is lambda nonlocal not or pass raise "
        "return try while with yield True False None"
    ).split()
    BUILTINS = (
        "abs all any bool bytes callable chr dict dir enumerate eval filter float "
        "format getattr hasattr hash hex id input int isinstance issubclass iter "
        "len list map max min next object open ord pow print range repr reversed "
        "round set setattr slice sorted str sum super tuple type vars zip"
    ).split()

    def __init__(self, document):
        super().__init__(document)
        self.keyword_fmt = self._format("teal_light", bold=True)
        self.builtin_fmt = self._format("ice")
        self.self_fmt = self._format("ice_light", italic=True)
        self.name_fmt = self._format("text_dark", bold=True)
        self.string_fmt = self._format("success")
        self.comment_fmt = self._format("text_muted", italic=True)
        self.number_fmt = self._format("coral")
        self.decorator_fmt = self._format("warning")
        self.rules = [
            (QRegularExpression(r"\b(?:def|class)\s+([A-Za-z_]\w*)"), self.name_fmt, 1),
            (QRegularExpression(r"\b(?:" + "|".join(self.KEYWORDS) + r")\b"), self.keyword_fmt, 0),
            (QRegularExpression(r"\b(?:" + "|".join(self.BUILTINS) + r")\b"), self.builtin_fmt, 0),
            (QRegularExpression(r"\bself\b"), self.self_fmt, 0),
            (QRegularExpression(r"#[^\n]*"), self.comment_fmt, 0),
            (QRegularExpression(r'"(?:[^"\\\n]|\\.)*"'), self.string_fmt, 0),
            (QRegularExpression(r"'(?:[^'\\\n]|\\.)*'"), self.string_fmt, 0),
            (QRegularExpression(r"\b(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?)\b"), self.number_fmt, 0),
            (QRegularExpression(r"@\w+(?:\.\w+)*"), self.decorator_fmt, 0),
        ]
        self.dq_open = QRegularExpression('"""')
        self.dq_close = QRegularExpression('"""')
        self.sq_open = QRegularExpression("'''")
        self.sq_close = QRegularExpression("'''")

    @staticmethod
    def _format(color, bold=False, italic=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(COLORS[color]))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def highlightBlock(self, text):
        self.setCurrentBlockState(self.STATE_NORMAL)
        for regex, fmt, index in self.rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(
                    match.capturedStart(index), match.capturedLength(index), fmt
                )

        start = 0
        prev = self.previousBlockState()
        if prev in (self.STATE_DQ, self.STATE_SQ):
            closer = self.dq_close if prev == self.STATE_DQ else self.sq_close
            match = closer.match(text, 0)
            if not match.hasMatch():
                self.setCurrentBlockState(prev)
                self.setFormat(0, len(text), self.string_fmt)
                return
            self.setFormat(0, match.capturedEnd(), self.string_fmt)
            start = match.capturedEnd()

        pairs = (
            (self.dq_open, self.dq_close, self.STATE_DQ),
            (self.sq_open, self.sq_close, self.STATE_SQ),
        )
        for opener, closer, state in pairs:
            pos = start
            while True:
                match = opener.match(text, pos)
                if not match.hasMatch():
                    break
                begin = match.capturedStart()
                end = closer.match(text, begin + 3)
                if not end.hasMatch():
                    self.setCurrentBlockState(state)
                    self.setFormat(begin, len(text) - begin, self.string_fmt)
                    return
                self.setFormat(begin, end.capturedEnd() - begin, self.string_fmt)
                pos = end.capturedEnd()


class AbyssalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Abyssal")
        self.resize(1100, 720)
        self.root_dir = os.getcwd()
        self.current_path = None

        self.editor = CodeEditor()
        self.highlighter = PythonHighlighter(self.editor.document())
        self.editor.document().modificationChanged.connect(self.sync_title)
        self.editor.cursorPositionChanged.connect(self.update_status)
        self.editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
                border: none;
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_md']}px;
                selection-background-color: {COLORS['selected']};
                selection-color: {COLORS['text_dark']};
            }}
        """)
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))

        self.model = QFileSystemModel(self)
        self.model.setRootPath(self.root_dir)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_dir))
        for column in range(1, 4):
            self.tree.hideColumn(column)
        self.tree.setHeaderHidden(True)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.AscendingOrder)
        self.tree.doubleClicked.connect(self.open_from_tree)
        self.tree.setStyleSheet(f"""
            QTreeView {{
                background-color: {COLORS['bg_mid']};
                color: {COLORS['text']};
                border: none;
                font-family: "{FONTS['ui']}";
                font-size: {FONTS['size_sm']}px;
                outline: 0;
            }}
            QTreeView::item {{ padding: 4px; }}
            QTreeView::item:hover {{ background: {COLORS['hover']}; }}
            QTreeView::item:selected {{
                background: {COLORS['selected']};
                color: {COLORS['text_dark']};
            }}
        """)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.editor)
        self.splitter.setSizes([260, 840])
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(f"QSplitter::handle {{ background: {COLORS['border']}; }}")

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)
        self.setCentralWidget(central)
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLORS['bg_dark']}; }}")

        self.file_label = QLabel("Untitled")
        self.pos_label = QLabel("Ln 1, Col 1")
        label_style = f"""
            font-size: {FONTS['size_xs']}px;
            padding: 2px 8px;
            background: transparent;
        """
        self.file_label.setStyleSheet(f"color: {COLORS['text_muted']}; {label_style}")
        self.pos_label.setStyleSheet(f"color: {COLORS['ice']}; {label_style}")
        self.statusBar().addWidget(self.file_label)
        self.statusBar().addPermanentWidget(self.pos_label)
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['bg_mid']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)

        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_file)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_file)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_file)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, activated=self.save_file_as)

    def new_file(self):
        if not self.confirm_discard():
            return
        self.editor.clear()
        self.current_path = None
        self.editor.document().setModified(False)
        self.sync_title(False)

    def open_file(self):
        if not self.confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open File", self.root_dir)
        if path:
            self.load_path(path)

    def open_from_tree(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            return
        if not self.confirm_discard():
            return
        self.load_path(path)

    def load_path(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                self.editor.setPlainText(handle.read())
        except OSError as exc:
            QMessageBox.critical(self, "Abyssal", f"Could not open file:\n{exc}")
            return
        self.current_path = path
        self.editor.document().setModified(False)
        self.sync_title(False)

    def save_file(self):
        if self.current_path is None:
            return self.save_file_as()
        try:
            with open(self.current_path, "w", encoding="utf-8") as handle:
                handle.write(self.editor.toPlainText())
        except OSError as exc:
            QMessageBox.critical(self, "Abyssal", f"Could not save file:\n{exc}")
            return False
        self.editor.document().setModified(False)
        self.sync_title(False)
        return True

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", self.current_path or self.root_dir
        )
        if not path:
            return False
        self.current_path = path
        return self.save_file()

    def confirm_discard(self):
        if not self.editor.document().isModified():
            return True
        ret = QMessageBox.question(
            self,
            "Abyssal",
            "Save changes to the current file?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if ret == QMessageBox.StandardButton.Save:
            return self.save_file()
        return ret == QMessageBox.StandardButton.Discard

    def sync_title(self, _modified=False):
        name = os.path.basename(self.current_path) if self.current_path else "Untitled"
        star = " •" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"Abyssal — {name}{star}")
        self.file_label.setText(self.current_path or "Untitled")

    def update_status(self):
        cursor = self.editor.textCursor()
        self.pos_label.setText(
            f"Ln {cursor.blockNumber() + 1}, Col {cursor.columnNumber() + 1}"
        )

    def closeEvent(self, event):
        if self.confirm_discard():
            event.accept()
        else:
            event.ignore()