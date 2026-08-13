

class DialogService:
    def __init__(self, config_dir: str) -> None:
        self._config_dir = config_dir

    def message_box(self, title: str, message: str,
                     buttons: list = None, icon: str = "info") -> str | None:
        pass

    def open_file(self, title: str = "Open File",
                  filters: str = "All Files (*)") -> str | None:
        pass

    def save_file(self, title: str = "Save File As") -> str | None:
        pass

    def show_about(self) -> dict[str, str]:
        return {
            "title": "Abyssal",
            "version": "2.0.0",
            "description": "High-density, low-latency text editor for Chomp OS",
            "framework": "PyQt5",
            "architecture": "VS Code-inspired workbench",
        }