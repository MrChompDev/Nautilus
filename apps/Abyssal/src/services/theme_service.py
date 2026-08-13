

class ThemeService:
    def __init__(self) -> None:
        self._theme_name = "dark"
        self._custom_overrides: dict = {}

    def load_theme(self, theme_name: str) -> None:
        self._theme_name = theme_name

    def get_theme_name(self) -> str:
        return self._theme_name

    def set_override(self, key: str, value: str) -> None:
        self._custom_overrides[key] = value

    def get_override(self, key: str, default: str | None = None) -> str | None:
        return self._custom_overrides.get(key, default)

    def get_all_overrides(self) -> dict:
        return dict(self._custom_overrides)