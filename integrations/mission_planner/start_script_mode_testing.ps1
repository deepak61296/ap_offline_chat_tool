# Quick Start Script for Script Mode Testing

Write-Host "`n=================================================="  -ForegroundColor Cyan
Write-Host "  Script Mode Testing - Quick Start" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

# Check if Mission Planner build exists
Write-Host "[1/4] Checking Mission Planner build..." -ForegroundColor Yellow
if (Test-Path "bin\Debug\net461\MissionPlanner.exe") {
    Write-Host "   ✓ Mission Planner build found`n" -ForegroundColor Green
}
else {
    Write-Host "   ✗ Mission Planner build not found!" -ForegroundColor Red
    Write-Host "   Please build Mission Planner first`n" -ForegroundColor Red
    exit 1
}

# Ensure Scripts directory exists
Write-Host "[2/4] Checking Scripts directory..." -ForegroundColor Yellow
if (!(Test-Path "Scripts\LuaScripts")) {
    New-Item -ItemType Directory -Path "Scripts\LuaScripts" -Force | Out-Null
    Write-Host "   ✓ Created Scripts/LuaScripts directory`n" -ForegroundColor Green
}
else {
    Write-Host "   ✓ Scripts/LuaScripts directory exists`n" -ForegroundColor Green
}

# Start Ollama
Write-Host "[3/4] Starting Ollama service..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ollama serve"
Write-Host "   ✓ Ollama window opened`n" -ForegroundColor Green
Start-Sleep -Seconds 3

# Start AI Backend
Write-Host "[4/4] Starting AI Backend..." -ForegroundColor Yellow
$backendPath = "C:\Projects\ardupilot-ai-backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $backendPath; python -m backend.api_server"
Write-Host "   ✓ Backend window opened`n" -ForegroundColor Green

# Wait for services
Write-Host "Waiting 10 seconds for services to initialize...`n" -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Launch Mission Planner
Write-Host "==================================================`n" -ForegroundColor Cyan
Write-Host "✓ Launching Mission Planner...`n" -ForegroundColor Green
Start-Process "bin\Debug\net461\MissionPlanner.exe"

Write-Host "==================================================`n" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Wait for Mission Planner to open" -ForegroundColor White
Write-Host "2. Press Ctrl+L to open Chat Assistant" -ForegroundColor White
Write-Host "3. Select 'Script' mode from dropdown" -ForegroundColor White
Write-Host "4. Try: 'create a script to monitor battery voltage'`n" -ForegroundColor White
Write-Host "==================================================`n" -ForegroundColor Cyan
