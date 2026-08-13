from apps.Abyssal.src.core.command import CommandRegistry
from apps.Abyssal.src.core.config import ConfigurationService
from apps.Abyssal.src.core.context import ContextKeyService
from apps.Abyssal.src.core.event_bus import EventBus
from apps.Abyssal.src.core.keybinding import KeybindingService
from apps.Abyssal.src.core.lifecycle import LifecycleService
from apps.Abyssal.src.core.service_container import ServiceContainer
from apps.Abyssal.src.services.dialog_service import DialogService
from apps.Abyssal.src.services.file_service import FileService
from apps.Abyssal.src.services.notification_service import NotificationService
from apps.Abyssal.src.services.terminal_service import TerminalService
from apps.Abyssal.src.services.theme_service import ThemeService


def register_services(config_dir: str) -> ServiceContainer:
    container = ServiceContainer()

    event_bus = EventBus()
    container.register("event_bus", event_bus)

    commands = CommandRegistry()
    container.register("commands", commands)

    keybindings = KeybindingService()
    container.register("keybindings", keybindings)

    config = ConfigurationService(config_dir)
    container.register("config", config)

    context = ContextKeyService()
    container.register("context", context)

    lifecycle = LifecycleService()
    container.register("lifecycle", lifecycle)

    file_service = FileService(config_dir)
    container.register("file_service", file_service)

    terminal_service = TerminalService()
    container.register("terminal_service", terminal_service)

    theme_service = ThemeService()
    container.register("theme_service", theme_service)

    notifications = NotificationService()
    container.register("notifications", notifications)

    dialog_service = DialogService(config_dir)
    container.register("dialog_service", dialog_service)

    return container