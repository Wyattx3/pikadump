@echo off
chcp 65001 >nul
echo === Telegram Card Extractor ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import pyrogram" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo.
echo === Starting Card Extractor ===
echo.
python main.py
pause
