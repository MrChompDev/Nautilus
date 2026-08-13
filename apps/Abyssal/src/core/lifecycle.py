from collections.abc import Callable


class LifecyclePhase:
    STARTING = "starting"
    STARTUP = "startup"
    READY = "ready"
    SHUTDOWN = "shutdown"


class LifecycleService:
    def __init__(self) -> None:
        self._phase = LifecyclePhase.STARTING
        self._listeners: list[Callable] = []

    @property
    def phase(self) -> str:
        return self._phase

    def startup(self) -> None:
        self._phase = LifecyclePhase.STARTUP
        self._notify()

    def ready(self) -> None:
        self._phase = LifecyclePhase.READY
        self._notify()

    def shutdown(self) -> None:
        self._phase = LifecyclePhase.SHUTDOWN
        self._notify()

    def is_ready(self) -> bool:
        return self._phase == LifecyclePhase.READY

    def is_active(self) -> bool:
        return self._phase in (LifecyclePhase.STARTUP, LifecyclePhase.READY)

    def on_phase_change(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def _notify(self) -> None:
        for callback in self._listeners:
            try:
                callback(self._phase)
            except Exception:
                pass