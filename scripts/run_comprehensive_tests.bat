@echo off
REM Run full test suite

echo ========================================
echo ArduPilot AI Backend - Full Test Suite
echo 150+ Tests with HTML Report
echo ========================================
echo.

REM Check backend
curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Backend not running!
    echo Start with: scripts\start_backend.bat
    pause
    exit /b 1
)

echo Backend running - starting comprehensive suite...
echo This will take ~8-12 minutes
echo.

call conda activate ai_backend
python tests\test_comprehensive.py

if exist tests\test_report.html (
    echo.
    echo Opening report...
    start tests\test_report.html
)

pause
