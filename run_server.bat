@echo off
REM Start Flask Server for Tech Job Intelligence Platform

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting Flask server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python server.py
