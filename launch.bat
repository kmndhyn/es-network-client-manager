@echo off
cd /d "%~dp0"

set VENV_DIR=.venv
set PYTHON=%VENV_DIR%\Scripts\python.exe
set PIP=%VENV_DIR%\Scripts\pip.exe
set REQ=requirements.txt
set PORT=8000
set HOST=127.0.0.1

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

echo Installing dependencies...
"%PIP%" install -r "%REQ%" --quiet

echo.
echo Client Manager: http://%HOST%:%PORT%
echo.
echo Keep this window open. Press Ctrl+C to stop.
echo.

"%PYTHON%" -m uvicorn main:app --host "%HOST%" --port "%PORT%"
pause
