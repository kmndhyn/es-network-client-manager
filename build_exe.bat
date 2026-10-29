@echo off
setlocal
chcp 65001 >nul
echo ========================================
echo Build ES Network Client Manager EXE
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Install Python 3.9+ from python.org and run this again.
    pause
    exit /b 1
)

echo [1/3] Installing build dependencies...
python -m pip install -r requirements.txt -q
if errorlevel 1 goto :fail

echo.
echo [2/3] Building single-file executable...
python -m PyInstaller --noconfirm --clean "ES Client Manager (single file).spec"
if errorlevel 1 goto :fail

echo.
echo [3/3] Building folder version (fallback if the single file is slow)...
python -m PyInstaller --noconfirm --clean "ES Client Manager.spec"
if errorlevel 1 goto :fail

echo.
echo ========================================
echo Build complete!
echo   Single file: dist\ES Client Manager.exe
echo   Folder:      dist\ES Client Manager\
echo ========================================
echo.
echo Distribute the single .exe, or zip the folder version.
echo Users double-click it; the app opens in its own window.
echo.
pause
exit /b 0

:fail
echo.
echo Build failed. Scroll up for the first error.
pause
exit /b 1
