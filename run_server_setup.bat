@echo off
REM Tech Job Intelligence Platform - Setup and Run Guide
REM Windows Batch Script

echo.
echo ===============================================
echo   Tech Job Intelligence Platform
echo   Modern Web Application Setup
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [OK] Python is installed

REM Check if venv exists
if not exist "venv\" (
    echo.
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Install requirements
echo.
echo [INFO] Installing Python packages...
echo This may take a few minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)
echo [OK] All packages installed successfully

REM Show startup information
echo.
echo ===============================================
echo   ✅ Setup Complete!
echo ===============================================
echo.
echo [INFO] Starting Flask Server...
echo.
echo Server Details:
echo - URL: http://localhost:5000
echo - Pages:
echo   - Home: http://localhost:5000/
echo   - Recommendations: http://localhost:5000/recommendations
echo   - Dashboard: http://localhost:5000/dashboard
echo   - Saved Jobs: http://localhost:5000/saved-jobs
echo.
echo [INFO] Server is starting...
echo Press Ctrl+C to stop the server
echo.
echo ===============================================
echo.

REM Start Flask server
python server.py

pause
