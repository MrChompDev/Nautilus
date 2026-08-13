import json
import os
from typing import Any


class ConfigurationSchema:
    def __init__(self) -> None:
        self._defaults: dict[str, Any] = {}
        self._descriptions: dict[str, str] = {}

    def define(self, key: str, default: Any, description: str = "") -> None:
        self._defaults[key] = default
        self._descriptions[key] = description

    def get_defaults(self) -> dict[str, Any]:
        return dict(self._defaults)

    def get_description(self, key: str) -> str:
        return self._descriptions.get(key, "")


class ConfigurationService:
    def __init__(self, config_dir: str) -> None:
        self._config_dir = config_dir
        self._settings: dict[str, Any] = {}
        self._schema = ConfigurationSchema()
        self._config_path = os.path.join(config_dir, "settings.json")
        self._workspace_config_path = os.path.join(config_dir, "workspace.json")

    def define_setting(self, key: str, default: Any, description: str = "") -> None:
        self._schema.define(key, default, description)

    def get(self, key: str, default: Any = None) -> Any:
        if key not in self._settings:
            return self._schema.get_defaults().get(key, default)
        return self._settings[key]

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value
        self._persist()

    def get_all(self) -> dict[str, Any]:
        defaults = self._schema.get_defaults()
        merged = dict(defaults)
        merged.update(self._settings)
        return merged

    def reload(self) -> None:
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path) as f:
                    loaded = json.load(f)
                    self._settings.update(loaded)
            except Exception:
                pass

    def _persist(self) -> None:
        os.makedirs(self._config_dir, exist_ok=True)
        try:
            with open(self._config_path, "w") as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass