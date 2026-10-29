@echo off
chcp 65001 >nul
echo ========================================
echo Build ES Network Client Manager EXE
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.9+ from python.org and try again.
    pause
    exit /b 1
)

echo [1/3] Installing PyInstaller...
pip install pyinstaller==6.14.0 -q

echo.
echo [2/3] Building executable...
pyinstaller ^
    --name "ES Client Manager" ^
    --windowed ^
    --add-data "static;static" ^
    --add-data "uploads;uploads" ^
    --add-data "database.py;." ^
    --add-data "main.py;." ^
    --hidden-import=uvicorn ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=uvicorn.loops ^
    --hidden-import=uvicorn.loops.auto ^
    --hidden-import=uvicorn.protocols ^
    --hidden-import=uvicorn.protocols.http ^
    --hidden-import=uvicorn.protocols.http.auto ^
    --hidden-import=uvicorn.protocols.websockets ^
    --hidden-import=uvicorn.protocols.websockets.auto ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=sqlalchemy ^
    --hidden-import=fastapi ^
    --hidden-import=pydantic ^
    launcher.py

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Copying distribution files...
if not exist "dist\ES Client Manager\static" mkdir "dist\ES Client Manager\static"
if not exist "dist\ES Client Manager\uploads" mkdir "dist\ES Client Manager\uploads"

xcopy /E /I /Y "static\*" "dist\ES Client Manager\static\" >nul
xcopy /E /I /Y "uploads\*" "dist\ES Client Manager\uploads\" >nul

echo.
echo ========================================
echo Build complete!
echo Output: dist\ES Client Manager\
echo ========================================
echo.
echo To distribute: zip the "dist\ES Client Manager" folder.
echo To run: double-click "ES Client Manager.exe" inside it.
echo.
pause
