@echo off
REM Run comprehensive automated tests for ArduPilot AI Backend

echo ========================================
echo ArduPilot AI Backend - Automated Tests
echo ========================================
echo.

REM Check if backend is running
echo Checking if backend is running...
curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Backend is not running!
    echo Please start the backend first with: scripts\start_backend.bat
    echo.
    pause
    exit /b 1
)

echo Backend is running - starting tests...
echo.

REM Activate conda environment
call conda activate ai_backend

REM Run tests
python tests\test_all_functions.py

REM Open report in browser
if exist test_report.html (
    echo.
    echo Opening test report in browser...
    start test_report.html
)

echo.
echo Tests complete!
pause
