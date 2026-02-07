@echo off
echo ========================================
echo ArduPilot AI Backend Server
echo Agent + Ask + Script Modes
echo ========================================
echo.
echo Starting backend on http://localhost:5000
echo.

cd /d "%~dp0"
call conda activate ai_backend
python run_server.py

pause
