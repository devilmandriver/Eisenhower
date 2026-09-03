@echo off
setlocal enabledelayedexpansion

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Eisenhower.spec del Eisenhower.spec

echo Installing dependencies...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
python -m pip install -r requirements.txt pyinstaller pillow >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install build dependencies.
    pause
    exit /b 1
)

echo Generating icon...
python build_icon.py
if errorlevel 1 (
    echo ERROR: Icon generation failed.
    pause
    exit /b 1
)

echo Building Eisenhower.exe (this may take up to a minute, please wait)...
python -m PyInstaller --onefile --windowed --name "Eisenhower" --icon=icon.ico ^
    --hidden-import=pkgutil ^
    --hidden-import=PySide6.sip ^
    --collect-all=PySide6 ^
    main.py --clean
if errorlevel 1 (
    echo ERROR: PyInstaller build failed. See output above for details.
    pause
    exit /b 1
)

if not exist "dist\Eisenhower.exe" (
    echo ERROR: Build failed. See output above for details.
    pause
    exit /b 1
)

echo.
echo Creating desktop shortcut...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Eisenhower.lnk'); $s.TargetPath = '%~dp0dist\Eisenhower.exe'; $s.WorkingDirectory = '%~dp0dist'; $s.Save()"

echo.
echo Done! Executable: dist\Eisenhower.exe
echo       Shortcut:   Desktop\Eisenhower.lnk
pause
