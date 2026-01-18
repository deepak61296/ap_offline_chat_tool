@echo off
REM Run ULTIMATE comprehensive test suite - merged baseline + mega

echo ========================================
echo ArduPilot AI Backend - ULTIMATE TESTS
echo 170+ Comprehensive Tests with HTML Report
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

call conda activate ap_chat_tools
python tests\test_comprehensive.py

if exist tests\test_report.html (
    echo.
    echo Opening report...
    start tests\test_report.html
)

pause
