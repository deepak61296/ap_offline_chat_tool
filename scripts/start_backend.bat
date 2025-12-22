@echo off
REM Start ArduPilot AI Backend with RAG

echo ========================================
echo ArduPilot AI Backend Startup
echo ========================================
echo.

REM Activate conda environment
call conda activate ap_chat_tools

REM Navigate to backend directory
cd /d C:\Projects\ArduPilot-AI-Backend\ap_offline_chat_tool

echo Starting AI Backend with RAG support...
echo.

REM Start the API server (using module syntax)
python -m backend.api_server

pause
