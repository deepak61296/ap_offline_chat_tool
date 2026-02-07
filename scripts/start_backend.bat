@echo off
REM Start ArduPilot AI Backend with RAG

echo ========================================
echo ArduPilot AI Backend Startup
echo ========================================
echo.

REM Activate conda environment
call conda activate ai_backend

REM Navigate to backend directory
cd /d C:\Projects\ardupilot-ai-backend

echo Starting AI Backend with RAG support...
echo.

REM Start the API server (using module syntax)
python -m backend.api_server

pause
