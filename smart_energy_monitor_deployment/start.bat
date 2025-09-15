@echo off
title Smart Energy Monitor vv1.0.0
echo.
echo 🏠 Smart Energy Monitor vv1.0.0
echo ================================================
echo AI-powered home energy monitoring system
echo Categories: Local Agent + For Humanity
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if this is first run
if not exist "data" (
    echo 🔧 First run detected - running setup...
    python install.py
    if errorlevel 1 (
        echo ❌ Setup failed
        pause
        exit /b 1
    )
)

echo 🚀 Starting Smart Energy Monitor...
echo Open your browser to: http://localhost:5000
echo Press Ctrl+C to stop
echo.

python app.py
pause
