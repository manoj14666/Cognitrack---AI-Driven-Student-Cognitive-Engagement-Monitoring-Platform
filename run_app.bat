@echo off
echo Cognitrack - Student Cognitive Engagement Monitoring Platform
echo ==============================================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found. Starting application...
echo.
echo The application will start in your default browser.
echo If it doesn't open automatically, go to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo.

cd backend
python app.py

pause
