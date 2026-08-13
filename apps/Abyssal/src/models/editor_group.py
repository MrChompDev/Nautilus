from typing import Optional

from apps.Abyssal.src.models.text_document import TextDocument


class EditorGroup:
    def __init__(self, group_id: int = 0) -> None:
        self.group_id = group_id
        self._documents: dict[str, TextDocument] = {}
        self._active_path: str | None = None
        self._order: list[str] = []

    def add_document(self, path: str, document: 'TextDocument') -> None:
        if path not in self._documents:
            self._documents[path] = document
            self._order.append(path)
        self._active_path = path

    def remove_document(self, path: str) -> None:
        self._documents.pop(path, None)
        if path in self._order:
            self._order.remove(path)
        if self._active_path == path:
            self._active_path = self._order[-1] if self._order else None

    def get_active(self) -> Optional['TextDocument']:
        if self._active_path and self._active_path in self._documents:
            return self._documents[self._active_path]
        return None

    def activate(self, path: str) -> Optional['TextDocument']:
        if path in self._documents:
            self._active_path = path
            return self._documents[path]
        return None

    def get_document(self, path: str) -> Optional['TextDocument']:
        return self._documents.get(path)

    def get_all_documents(self) -> dict[str, 'TextDocument']:
        return dict(self._documents)

    def get_order(self) -> list[str]:
        return list(self._order)

    def has_document(self, path: str) -> bool:
        return path in self._documents

    @property
    def count(self) -> int:
        return len(self._documents)

    @property
    def active_path(self) -> str | None:
        return self._active_path