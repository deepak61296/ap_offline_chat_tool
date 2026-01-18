@echo off
REM Run MEGA comprehensive test suite for ArduPilot AI Backend

echo ========================================
echo ArduPilot AI Backend - MEGA TEST SUITE
echo 200+ Comprehensive Human-Like Tests
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

echo Backend is running - starting MEGA test suite...
echo.
echo [INFO] This will take ~10-15 minutes for 200+ tests
echo.

REM Activate conda environment
call conda activate ap_chat_tools

REM Run mega test suite
python tests\test_mega_suite.py

echo.
echo MEGA Test Suite Complete!
echo.
echo Check results above for detailed pass/fail breakdown
pause
