from collections.abc import Callable
from typing import Any


class Command:
    def __init__(self, id: str, label: str, handler: Callable,
                 description: str = "", shortcut: str = "") -> None:
        self.id = id
        self.label = label
        self.handler = handler
        self.description = description
        self.shortcut = shortcut


class CommandRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._commands: dict[str, Command] = {}
            cls._instance._executing = False
        return cls._instance

    def register(self, command: Command) -> None:
        self._commands[command.id] = command

    def unregister(self, command_id: str) -> None:
        self._commands.pop(command_id, None)

    def get(self, command_id: str) -> Command | None:
        return self._commands.get(command_id)

    def list_commands(self) -> list[Command]:
        return list(self._commands.values())

    def execute(self, command_id: str, *args: Any) -> Any:
        command = self._commands.get(command_id)
        if command is None:
            return None
        self._executing = True
        try:
            return command.handler(*args)
        finally:
            self._executing = False

    def is_executing(self) -> bool:
        return self._executing


def register_command(command_id: str, label: str, shortcut: str = "") -> Callable:
    def decorator(fn: Callable) -> Callable:
        cmd = Command(command_id, fn.__name__, fn, shortcut=shortcut)
        cmd.label = label
        CommandRegistry().register(cmd)
        return fn
    return decorator


def execute_command(command_id: str, *args: Any) -> Any:
    return CommandRegistry().execute(command_id, *args)