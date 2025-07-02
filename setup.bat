@echo off
echo Setting up PDF to HTML Converter...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To run the server:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Run server: python src\Backend\server.py
echo.
echo The server will be available at: http://localhost:8000
echo Frontend should be at: http://localhost:5173
echo.
pause
