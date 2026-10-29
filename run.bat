@echo off
rem Nautilus OS — one-click launcher (Windows, 64-bit Python required)
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    if not exist "python" (
        echo No Python found. Install Python 3.11+ 64-bit first.
        pause
        exit /b 1
    )
    set "PY=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating venv...
    %PY% -m venv .venv || goto :fail
)

.venv\Scripts\python.exe -c "import PySide6" 2>nul || (
    echo Installing requirements...
    .venv\Scripts\python.exe -m pip install --quiet -r requirements.txt || goto :fail
)

.venv\Scripts\python.exe core\main.py %*
goto :eof

:fail
echo.
echo Launch failed. Make sure you are running 64-bit Python 3.11+.
pause
