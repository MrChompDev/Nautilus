"""
Nautilus OS — Qt Runtime Environment Setup
Ensures Qt plugins and their dependent DLLs are discoverable before a
QApplication is created.

Fixes plugin-backed image formats (e.g. SVG via qsvg.dll) failing to load
in sandboxed / WindowsApps Python installations where Qt cannot resolve
sibling Qt DLLs such as Qt6Svg.dll during plugin load.
"""

import os


def setup_qt_environment():
    """Add each installed Qt binding's directory to the DLL search path and
    register its plugin directory in QT_PLUGIN_PATH. Safe to call multiple
    times and a no-op when the bindings are absent."""
    for name in ("PySide6", "PyQt6", "PyQt5"):
        try:
            module = __import__(name)
        except ImportError:
            continue

        pkg_dir = os.path.dirname(module.__file__)
        if not pkg_dir:
            continue

        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(pkg_dir)
            except OSError:
                pass

        plugins_dir = os.path.join(pkg_dir, "plugins")
        if os.path.isdir(plugins_dir):
            current = os.environ.get("QT_PLUGIN_PATH", "")
            entries = [e for e in current.split(os.pathsep) if e]
            if plugins_dir not in entries:
                entries.insert(0, plugins_dir)
                os.environ["QT_PLUGIN_PATH"] = os.pathsep.join(entries)
