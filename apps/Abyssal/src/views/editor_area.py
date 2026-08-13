
from PySide6.QtWidgets import QVBoxLayout, QWidget

from apps.Abyssal.src.models.text_document import TextDocument


class TextEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._document: TextDocument | None = None
        self._file_path: str | None = None
        self._language: str = "text"
        self._modified: bool = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addStretch(1)
        self.setLayout(layout)

    def load_document(self, document: TextDocument) -> None:
        self._document = document
        self._file_path = document.file_path
        self._language = document.language
        self._modified = document.is_modified

    def get_document(self) -> TextDocument | None:
        return self._document

    def get_file_path(self) -> str | None:
        return self._file_path

    def get_language(self) -> str:
        return self._language

    def is_modified(self) -> bool:
        return self._modified

    def save(self) -> bool:
        if self._document and self._file_path:
            return self._document.save()
        return False


class EditorArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._editors: dict = {}
        self._active_path: str | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def add_editor(self, path: str, editor_widget: TextEditorWidget) -> None:
        self._editors[path] = editor_widget
        self._active_path = path

    def remove_editor(self, path: str) -> None:
        self._editors.pop(path, None)
        if path in self._editors:
            del self._editors[path]
        if self._active_path == path:
            self._active_path = None

    def activate_editor(self, path: str) -> TextEditorWidget | None:
        editor = self._editors.get(path)
        if editor:
            self._active_path = path
            for p, e in self._editors.items():
                e.setVisible(p == path)
        return editor

    def get_active_editor(self) -> TextEditorWidget | None:
        if self._active_path:
            return self._editors.get(self._active_path)
        return None

    def get_editor_count(self) -> int:
        return len(self._editors)

    def get_all_paths(self) -> list[str]:
        return list(self._editors.keys())