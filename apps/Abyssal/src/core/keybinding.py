
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


class Keybinding:
    def __init__(self, command_id: str, sequence: str,
                 context: str = "global") -> None:
        self.command_id = command_id
        self.sequence = sequence
        self.context = context
        self.shortcut = QKeySequence(sequence)


class KeybindingService:
    def __init__(self) -> None:
        self._bindings: dict[str, Keybinding] = {}
        self._context = "global"

    def register(self, command_id: str, sequence: str,
                 context: str = "global") -> None:
        binding = Keybinding(command_id, sequence, context)
        self._bindings[sequence] = binding

    def unregister(self, sequence: str) -> None:
        self._bindings.pop(sequence, None)

    def resolve(self, sequence: str) -> str | None:
        binding = self._bindings.get(sequence)
        if binding:
            return binding.command_id
        return None

    def get_all_bindings(self) -> dict[str, str]:
        result = {}
        for binding in self._bindings.values():
            result[str(binding.shortcut.toString())] = binding.command_id
        return result

    @staticmethod
    def from_qkeysequence(event) -> str | None:
        if hasattr(event, 'modifiers') and hasattr(event, 'key'):
            mods = int(event.modifiers())
            key = int(event.key())
            parts = []
            if mods & Qt.ControlModifier:
                parts.append("Ctrl")
            if mods & Qt.ShiftModifier:
                parts.append("Shift")
            if mods & Qt.AltModifier:
                parts.append("Alt")
            if mods & Qt.MetaModifier:
                parts.append("Meta")
            ks = QKeySequence(key)
            key_str = ks.toString(QKeySequence.NativeText)
            if key_str and key_str not in ("", "Backtab"):
                parts.append(key_str)
            return "+".join(parts)
        return None


_default_bindings = {
    "Ctrl+S": "workbench.action.files.save",
    "Ctrl+Shift+S": "workbench.action.files.saveAs",
    "Ctrl+N": "workbench.action.files.newFile",
    "Ctrl+O": "workbench.action.files.openFile",
    "Ctrl+Shift+P": "workbench.action.showCommands",
    "Ctrl+P": "workbench.action.quickOpen",
    "F5": "workbench.action.files.runFile",
    "Ctrl+R": "workbench.action.files.runFile",
    "Ctrl+B": "workbench.action.toggleSidebar",
    "Ctrl+`": "workbench.action.toggleTerminal",
    "Ctrl+F": "workbench.action.find",
    "Ctrl+H": "workbench.action.findAndReplace",
    "Ctrl+W": "workbench.action.closeEditor",
    "Escape": "workbench.action.closeFindBar",
}