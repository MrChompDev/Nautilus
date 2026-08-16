"""
Surfline Browser - Entry Point
Built for coders, by coders. Driven by performance.
"""
import os
import struct
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _is_64bit():
    return struct.calcsize("P") * 8 == 64


def _try_relaunch_with_64bit():
    """If running on 32-bit Python, find 64-bit Python and relaunch."""
    if _is_64bit():
        try:
            import PySide6  # noqa: F401 - 64-bit availability probe
            return True
        except ImportError:
            return False

    # We're on 32-bit - try to find py -3.13 (64-bit)
    import shutil
    py_exe = shutil.which("py")
    if py_exe:
        try:
            result = subprocess.run(
                [py_exe, "-3.13", "-c", "import PySide6; print('ok')"],
                capture_output=True, timeout=10, text=True
            )
            if result.returncode == 0 and "ok" in result.stdout:
                print("[Surfline] Switching to 64-bit Python 3.13...")
                script = os.path.join(SCRIPT_DIR, "main.py")
                proc = subprocess.Popen(
                    [py_exe, "-3.13", script] + sys.argv[1:],
                    cwd=SCRIPT_DIR
                )
                proc.wait()
                sys.exit(proc.returncode)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    print("[Surfline] ERROR: PySide6 requires 64-bit Python 3.13.")
    print("  Run: py -3.13 -m pip install PySide6")
    print("  Then: py -3.13 main.py")
    return False


if not _try_relaunch_with_64bit():
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.dirname(SCRIPT_DIR)))

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from apps.Surfline.src.icons import ensure_icons
from apps.Surfline.src.window import SurflineWindow
from core.theme import FONTS, get_global_stylesheet


def main():
    # Point Qt to the correct WebEngine resources directory
    import PySide6
    _pyside_dir = os.path.dirname(PySide6.__file__)
    _resources_dir = os.path.join(_pyside_dir, "resources")
    if os.path.isdir(_resources_dir):
        os.environ["QTWEBENGINE_RESOURCES_PATH"] = _resources_dir

    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--disable-background-networking "
        "--disable-default-apps "
        "--disable-extensions "
        "--disable-sync "
        "--disable-translate "
        "--disable-blink-features=AutomationControlled "
        "--enable-gpu-rasterization "
        "--enable-zero-copy "
        "--disable-smooth-scrolling"
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Surfline")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ChompOS")

    app.setStyleSheet(get_global_stylesheet())

    font = QFont()
    font.setFamilies([
        FONTS["ui"],
        FONTS["mono_fallback"],
        FONTS["mono_fallback2"],
        "Arial"
    ])
    font.setPointSize(FONTS["size_md"])
    app.setFont(font)

    ensure_icons()

    initial_url = None
    for arg in sys.argv[1:]:
        if arg.startswith(("http://", "https://", "file://")):
            initial_url = arg
            break

    window = SurflineWindow(initial_url=initial_url)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
