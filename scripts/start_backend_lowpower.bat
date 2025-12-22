@echo off
REM Start ArduPilot AI Backend in low-power mode (for less powerful CPUs)

echo ========================================
echo ArduPilot AI Backend - Low Power Mode
echo ========================================
echo.

REM Activate conda environment
call conda activate ap_chat_tools

REM Navigate to backend directory
cd /d C:\Projects\ArduPilot-AI-Backend\ap_offline_chat_tool

echo Starting AI Backend in low-power mode...
echo (Reduced context size, fewer doc chunks)
echo.

REM Start the API server with --low-power flag
python -m backend.api_server --no-gpu --low-power

pause
