import os

from PySide6.QtWidgets import QFileDialog

from apps.Abyssal.src.core.event_bus import emit


class FileService:
    def __init__(self, config_dir: str) -> None:
        self._config_dir = config_dir
        self._recent_files: list = []
        self._workspace_path: str = config_dir
        self._load_recent()

    def open_file(self, parent=None, path: str = None) -> dict:
        if path is None:
            path, _ = QFileDialog.getOpenFileName(
                parent, "Open File", self._get_default_directory(),
                "All Files (*);;Python (*.py);;JavaScript (*.js);;"
                "C/C++ (*.c *.cpp *.h);;HTML (*.html);;CSS (*.css);;"
                "Markdown (*.md);;JSON (*.json);;Shell (*.sh);;YAML (*.yaml *.yml)"
            )

        if not path:
            return {"accepted": False}

        result = self._read_file(path)
        if result["accepted"]:
            self._add_recent(path)
            emit("file.opened", result)
        return result

    def save_file(self, path: str, content: str) -> dict:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            result = {"accepted": True, "path": path}
            emit("file.saved", result)
            return result
        except Exception as e:
            return {"accepted": False, "path": path, "error": str(e)}

    def save_file_as(self, parent=None, content: str = "") -> dict:
        path, _ = QFileDialog.getSaveFileName(
            parent, "Save File As", self._get_default_directory(),
            "All Files (*);;Python (*.py);;JavaScript (*.js);;"
            "C/C++ (*.c *.cpp);;HTML (*.html);;CSS (*.css);;Markdown (*.md)"
        )
        if not path:
            return {"accepted": False}

        return self.save_file(path, content)

    def get_recent_files(self) -> list:
        return list(self._recent_files)

    def get_workspace_path(self) -> str:
        return self._workspace_path

    def set_workspace_path(self, path: str) -> None:
        self._workspace_path = path

    def _get_default_directory(self) -> str:
        return self._workspace_path if os.path.isdir(self._workspace_path) else ""

    def _read_file(self, path: str) -> dict:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            return {"accepted": True, "path": path, "content": content}
        except UnicodeDecodeError:
            try:
                with open(path, encoding="latin-1") as f:
                    content = f.read()
                return {"accepted": True, "path": path, "content": content}
            except Exception as e:
                return {"accepted": False, "path": path, "error": str(e)}
        except Exception as e:
            return {"accepted": False, "path": path, "error": str(e)}

    def _add_recent(self, path: str) -> None:
        self._recent_files = [p for p in self._recent_files if p != path]
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:20]
        self._save_recent()

    def _recent_path(self) -> str:
        return os.path.join(self._config_dir, "recent.json")

    def _load_recent(self) -> None:
        path = self._recent_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._recent_files = json.load(f)
            except Exception:
                pass

    def _save_recent(self) -> None:
        path = self._recent_path()
        try:
            os.makedirs(self._config_dir, exist_ok=True)
            with open(path, "w") as f:
                json.dump(self._recent_files, f, indent=2)
        except Exception:
            pass


import json