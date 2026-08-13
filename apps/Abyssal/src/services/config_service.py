import json
import os
import shutil
import threading
import time
from typing import Any

from PySide6.QtCore import QObject, Signal


class ConfigurationSchema:
    def __init__(self) -> None:
        self._defaults: dict[str, Any] = {}
        self._descriptions: dict[str, str] = {}
        self._callbacks: dict[str, list[Any]] = {}

    def define(self, key: str, default: Any, description: str = "", 
               callback: Any | None = None, callback_args: dict | None = None) -> None:
        self._defaults[key] = default
        self._descriptions[key] = description
        if callback:
            self._callbacks[key] = [callback, callback_args or {}]

    def get_defaults(self) -> dict[str, Any]:
        return dict(self._defaults)

    def get_description(self, key: str) -> str:
        return self._descriptions.get(key, "")

    def trigger_callback(self, key: str, old_value: Any, new_value: Any) -> None:
        if key in self._callbacks:
            callback, args = self._callbacks[key]
            if args is None:
                args = {}
            args.update({"key": key, "old_value": old_value, "new_value": new_value})
            callback(**args)


class ConfigurationService(QObject):
    settings_changed = Signal(str, object, object)

    def __init__(self, config_dir: str) -> None:
        super().__init__()
        self._config_dir = config_dir
        self._settings: dict[str, Any] = {}
        self._schema = ConfigurationSchema()
        self._config_path = os.path.join(config_dir, "settings.json")
        self._backup_dir = os.path.join(config_dir, "backups")
        self._lock = threading.RLock()
        self._observers: list[Any] = []

    def define_setting(self, key: str, default: Any, description: str = "",
                       callback: Any | None = None, callback_args: dict | None = None) -> None:
        with self._lock:
            old_value = self.get(key, None)
            self._schema.define(key, default, description, callback, callback_args)
            if old_value is None and self._config_path and os.path.exists(self._config_path):
                pass

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key not in self._settings:
                return self._schema.get_defaults().get(key, default)
            return self._settings[key]

    def set(self, key: str, value: Any, silent: bool = False) -> None:
        with self._lock:
            old_value = self.get(key, None)
            if old_value == value:
                return

            self._settings[key] = value
            self._persist()

            if not silent:
                self.settings_changed.emit(key, old_value, value)
                self._schema.trigger_callback(key, old_value, value)

    def get_all(self) -> dict[str, Any]:
        with self._lock:
            defaults = self._schema.get_defaults()
            merged = dict(defaults)
            merged.update(self._settings)
            return merged

    def reload(self) -> None:
        with self._lock:
            if os.path.exists(self._config_path):
                try:
                    with open(self._config_path) as f:
                        loaded = json.load(f)
                        self._settings.update(loaded)
                except Exception as e:
                    print(f"Error loading configuration: {e}")

    def _persist(self) -> None:
        os.makedirs(self._config_dir, exist_ok=True)
        try:
            with open(self._config_path, "w") as f:
                json.dump(self._settings, f, indent=2)
            self._create_backup()
        except Exception as e:
            print(f"Error persisting configuration: {e}")

    def backup(self, name: str = "") -> None:
        """Create a backup of current settings"""
        self._create_backup(name)

    def _create_backup(self, name: str = ""):
        os.makedirs(self._backup_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"settings_{timestamp}.json"
        if name:
            backup_name = f"settings_{name}.json"
        backup_path = os.path.join(self._backup_dir, backup_name)
        try:
            shutil.copy2(self._config_path, backup_path)
        except Exception:
            pass

    def restore(self, backup_name: str = "") -> bool:
        """Restore settings from backup"""
        backups = [f for f in os.listdir(self._backup_dir) if f.endswith('.json')]
        if not backups:
            return False

        if backup_name and backup_name + '.json' in backups:
            backup_file = backup_name + '.json'
        else:
            backup_file = backups[-1]

        backup_path = os.path.join(self._backup_dir, backup_file)
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, self._config_path)
                self.reload()
                return True
            except Exception:
                pass
        return False

    def get_backups(self) -> list[str]:
        """Get list of available backups"""
        if not os.path.exists(self._backup_dir):
            return []
        return [f for f in os.listdir(self._backup_dir) if f.endswith('.json')]

    def export(self, path: str) -> bool:
        """Export settings to a file"""
        try:
            with open(path, 'w') as f:
                json.dump(self._settings, f, indent=2)
            return True
        except Exception:
            return False

    def import_settings(self, path: str) -> bool:
        """Import settings from a file"""
        try:
            with open(path) as f:
                imported = json.load(f)
            with self._lock:
                self._settings.update(imported)
                self._persist()
            return True
        except Exception:
            return False

    def add_observer(self, observer: Any) -> None:
        """Add an observer that will be notified when settings change"""
        self._observers.append(observer)

    def remove_observer(self, observer: Any) -> None:
        """Remove an observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify all observers about a setting change"""
        for observer in self._observers:
            if hasattr(observer, 'on_setting_changed'):
                observer.on_setting_changed(key, old_value, new_value)
