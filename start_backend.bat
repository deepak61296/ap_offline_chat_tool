@echo off
echo ========================================
echo ArduPilot AI Backend Server V2.2
echo 21 Templates + LLM + Post-Processing
echo ========================================
echo.
echo Starting backend on http://localhost:5000
echo.

cd /d "%~dp0"
call conda activate ap_chat_tools
python run_server.py

pause
