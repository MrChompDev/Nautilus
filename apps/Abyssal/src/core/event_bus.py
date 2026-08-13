from collections.abc import Callable
from typing import Any


class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners: dict[str, list] = {}
        return cls._instance

    def subscribe(self, event: str, handler: Callable) -> None:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(handler)

    def unsubscribe(self, event: str, handler: Callable) -> None:
        if event in self._listeners:
            self._listeners[event].remove(handler)

    def emit(self, event: str, data: Any = None) -> None:
        for handler in self._listeners.get(event, []):
            try:
                handler(data)
            except Exception:
                pass


def on(event: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        EventBus().subscribe(event, fn)
        return fn
    return decorator


def emit(event: str, data: Any = None) -> None:
    EventBus().emit(event, data)