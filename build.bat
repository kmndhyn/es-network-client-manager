@echo off
cd /d "%~dp0"

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Install it with:
    echo   pip install pyinstaller
    echo.
    pause
    exit /b 1
)

echo Building standalone EXE...
pyinstaller --onefile --windowed ^
    --add-data "static;static" ^
    --hidden-import=database ^
    --name "ES-Client-Manager" ^
    main.py

echo.
echo Done. Check the dist\ folder for ES-Client-Manager.exe
echo.
pause
