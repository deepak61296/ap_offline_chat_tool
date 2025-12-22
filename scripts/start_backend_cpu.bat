@echo off
REM Start ArduPilot AI Backend with CPU-only mode (no GPU)

echo ========================================
echo ArduPilot AI Backend - CPU Only Mode
echo ========================================
echo.

REM Activate conda environment
call conda activate ap_chat_tools

REM Navigate to backend directory
cd /d C:\Projects\ArduPilot-AI-Backend\ap_offline_chat_tool

echo Starting AI Backend in CPU-only mode...
echo (Slower but works on any system)
echo.

REM Start the API server with --no-gpu flag
python -m backend.api_server --no-gpu

pause
