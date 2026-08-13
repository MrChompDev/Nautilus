@echo off
REM Surfline Browser - Launcher
REM Uses 64-bit Python for PySide6 compatibility

REM Try the 64-bit Python first
py -3.13 "%~dp0main.py" %* 2>nul
if %errorlevel% neq 0 (
    REM Fallback: try default python
    python "%~dp0main.py" %*
)
if %errorlevel% neq 0 (
    echo.
    echo [Surfline] Failed to start.
    echo   Install PySide6 with 64-bit Python:
    echo   py -3.13 -m pip install PySide6
    echo.
    pause
)
