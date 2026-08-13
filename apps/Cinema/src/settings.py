"""Cinema — local settings & favorites persistence (JSON)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass
class CinemaSettings:
    media_folders: list = field(default_factory=list)
    import_mode: str = "move"   # "move" | "copy" — what Import Media does with source files
    disclaimer_accepted: bool = False
    favorites: list = field(default_factory=list)

    @classmethod
    def load(cls, path: str) -> CinemaSettings:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            known = {x for x in cls.__dataclass_fields__}
            return cls(**{k: v for k, v in data.items() if k in known})
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return cls()

    def save(self, path: str):
        tmp = path + ".tmp"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2)
        os.replace(tmp, path)

    def is_favorite(self, item_id: str) -> bool:
        return item_id in self.favorites

    def toggle_favorite(self, item_id: str) -> bool:
        if item_id in self.favorites:
            self.favorites.remove(item_id)
            return False
        self.favorites.append(item_id)
        return True
