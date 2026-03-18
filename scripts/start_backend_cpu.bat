@echo off
REM Start ArduPilot AI Backend with CPU-only mode (no GPU)

echo ========================================
echo ArduPilot AI Backend - CPU Only Mode
echo ========================================
echo.

REM Activate conda environment
call conda activate ai_backend

REM Navigate to backend directory
cd /d C:\Projects\ardupilot-ai-backend

echo Starting AI Backend in CPU-only mode...
echo (Slower but works on any system)
echo.

REM Start the API server with --no-gpu flag
python -m backend.api_server --no-gpu

pause
