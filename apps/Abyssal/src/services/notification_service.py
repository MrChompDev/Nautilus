

class NotificationService:
    def __init__(self) -> None:
        self._notifications: list = []

    def show(self, message: str, severity: str = "info", timeout: int = 3000) -> None:
        notification = {
            "message": message,
            "severity": severity,
            "timeout": timeout,
        }
        self._notifications.append(notification)

    def info(self, message: str) -> None:
        self.show(message, "info")

    def warn(self, message: str) -> None:
        self.show(message, "warn")

    def error(self, message: str) -> None:
        self.show(message, "error")

    def get_notifications(self) -> list:
        return list(self._notifications)

    def clear(self) -> None:
        self._notifications.clear()