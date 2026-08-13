import json
import os
from typing import Any


class WorkspaceConfig:
    def __init__(self, config_dir: str) -> None:
        self._config_dir = config_dir
        self._path = os.path.join(config_dir, "workspace.json")
        self._data: dict[str, Any] = {
            "open_files": [],
            "current_file": None,
            "sidebar_visible": True,
            "terminal_visible": False,
            "geometry": "",
        }
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            try:
                with open(self._path) as f:
                    loaded = json.load(f)
                    self._data.update(loaded)
            except Exception:
                pass

    def _save(self) -> None:
        os.makedirs(self._config_dir, exist_ok=True)
        try:
            with open(self._path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._save()

    def get_open_files(self) -> list:
        return self._data.get("open_files", [])

    def set_open_files(self, files: list) -> None:
        self._data["open_files"] = files
        self._save()

    def get_current_file(self) -> str | None:
        return self._data.get("current_file")

    def set_current_file(self, path: str | None) -> None:
        self._data["current_file"] = path
        self._save()

    def is_sidebar_visible(self) -> bool:
        return self._data.get("sidebar_visible", True)

    def set_sidebar_visible(self, visible: bool) -> None:
        self._data["sidebar_visible"] = visible
        self._save()

    def is_terminal_visible(self) -> bool:
        return self._data.get("terminal_visible", False)

    def set_terminal_visible(self, visible: bool) -> None:
        self._data["terminal_visible"] = visible
        self._save()

    def get_geometry(self) -> str:
        return self._data.get("geometry", "")

    def set_geometry(self, geometry: str) -> None:
        self._data["geometry"] = geometry
        self._save()

    def update_editor_state(self, open_files: list, current_file: str | None) -> None:
        self._data["open_files"] = open_files
        self._data["current_file"] = current_file
        self._save()


def load_workspace(config_dir: str) -> WorkspaceConfig:
    return WorkspaceConfig(config_dir)


def save_workspace(config_dir: str) -> None:
    pass