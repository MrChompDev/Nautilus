from typing import Any


class ServiceContainer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services: dict[str, Any] = {}
            cls._instance._factories: dict[str, Any] = {}
        return cls._instance

    def register(self, name: str, service: Any, singleton: bool = True) -> None:
        if singleton:
            self._services[name] = service
        else:
            self._factories[name] = lambda: service

    def get(self, name: str) -> Any | None:
        if name in self._services:
            return self._services[name]
        factory = self._factories.get(name)
        if factory:
            return factory()
        return None

    def has(self, name: str) -> bool:
        return name in self._services or name in self._factories

    def resolve(self, cls: type) -> Any | None:
        for service in self._services.values():
            if isinstance(service, cls):
                return service
        return None