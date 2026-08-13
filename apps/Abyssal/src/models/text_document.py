import os

from PySide6.QtGui import QTextCursor, QTextDocument


class TextDocument:
    def __init__(self, file_path: str | None = None) -> None:
        self.file_path = file_path
        self._document = QTextDocument()
        self._language = "text"
        self._modified = False
        self._name = os.path.basename(file_path) if file_path else "Untitled"

        if file_path and os.path.exists(file_path):
            self._load(file_path)

    def _load(self, file_path: str) -> None:
        try:
            with open(file_path, encoding="utf-8") as f:
                self._document.setPlainText(f.read())
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as f:
                self._document.setPlainText(f.read())
        except Exception:
            pass

        self._language = self._detect_language(file_path)
        self._modified = False

    @staticmethod
    def _detect_language(file_path: str) -> str:
        from apps.Abyssal.src.engines.highlighter import detect_language
        return detect_language(file_path)

    @property
    def document(self) -> QTextDocument:
        return self._document

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        self._language = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_modified(self) -> bool:
        return self._modified

    def set_modified(self, value: bool) -> None:
        self._modified = value

    @property
    def line_count(self) -> int:
        return self._document.blockCount()

    def get_text(self) -> str:
        return self._document.toPlainText()

    def set_text(self, text: str) -> None:
        self._document.setPlainText(text)
        self._modified = True

    def insert_text(self, position: int, text: str) -> None:
        cursor = QTextCursor(self._document)
        cursor.setPosition(position)
        cursor.insertText(text)
        self._modified = True

    def delete_text(self, start: int, end: int) -> None:
        cursor = QTextCursor(self._document)
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        self._modified = True

    def get_text_at(self, block: int, column: int) -> str:
        cursor = QTextCursor(self._document)
        cursor.setPosition(block)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        block_start = cursor.position()
        cursor.setPosition(block_start + column, QTextCursor.KeepAnchor)
        return cursor.selectedText()[block_start:]

    def save(self) -> bool:
        if not self.file_path:
            return False
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self._document.toPlainText())
            self._modified = False
            return True
        except Exception:
            return False

    def save_as(self, new_path: str) -> bool:
        self.file_path = new_path
        self._name = os.path.basename(new_path)
        self._language = self._detect_language(new_path)
        return self.save()