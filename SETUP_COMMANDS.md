# Setup and Test Commands

Complete command reference for setting up and testing the ArduPilot AI Backend.

## Initial Setup

### 1. Install Ollama

**Windows:**
```powershell
# Download and install from official site
# Visit: https://ollama.com/download

# Verify installation
ollama --version
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

### 2. Pull LLM Models

```bash
# Core model for Agent/Ask modes (fast, 3B parameters)
ollama pull qwen2.5-coder:3b

# Script mode model (better code generation, 7B parameters)
ollama pull qwen2.5-coder:7b

# Verify models are downloaded
ollama list
```

Expected output:
```
NAME                    ID              SIZE      MODIFIED
qwen2.5-coder:3b        abc123def       1.9 GB    2 hours ago
qwen2.5-coder:7b        xyz789ghi       4.7 GB    2 hours ago
```

### 3. Create Conda Environment (Option 1 - New Environment)

```bash
# Create new environment with Python 3.10
conda create -n ardupilot_ai python=3.10 -y

# Activate environment
conda activate ardupilot_ai

# Navigate to project directory
cd C:\Projects\ardupilot-ai-backend

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import flask; import requests; print('Dependencies OK')"
```

### 4. Create Conda Environment (Option 2 - From Existing)

If you already have `ai_backend` environment and want a fresh start:

```bash
# Deactivate current environment (if active)
conda deactivate

# Remove old environment
conda env remove -n ai_backend

# Create new environment
conda create -n ardupilot_ai python=3.10 -y

# Activate new environment
conda activate ardupilot_ai

# Install dependencies
cd C:\Projects\ardupilot-ai-backend
pip install -r requirements.txt
```

### 5. Update Existing Environment

If you want to keep your existing environment but update it:

```bash
# Activate environment
conda activate ai_backend

# Update all packages
cd C:\Projects\ardupilot-ai-backend
pip install -r requirements.txt --upgrade

# Or force reinstall everything
pip install -r requirements.txt --force-reinstall
```

## Starting the Backend

### Standard Mode (with GPU if available)

```bash
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server
```

Or use the batch script:
```bash
cd C:\Projects\ardupilot-ai-backend
start_backend.bat
```

### CPU-Only Mode (no GPU)

```bash
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server --no-gpu
```

Or use the batch script:
```bash
cd C:\Projects\ardupilot-ai-backend\scripts
start_backend_cpu.bat
```

### Low-Power Mode (for older/weaker CPUs)

```bash
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server --no-gpu --low-power
```

Or use the batch script:
```bash
cd C:\Projects\ardupilot-ai-backend\scripts
start_backend_lowpower.bat
```

Expected output:
```
========================================
ArduPilot AI Backend Server
Agent + Ask + Script Modes
========================================

Starting backend on http://localhost:5000

Loading models...
✓ qwen2.5-coder:3b loaded
✓ qwen2.5-coder:7b loaded
Server running on http://localhost:5000
Press Ctrl+C to stop
```

## Verification Tests

### 1. Backend Health Check

```bash
# Test if backend is running
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "ollama_status": "connected",
  "models_loaded": ["qwen2.5-coder:3b", "qwen2.5-coder:7b"]
}
```

### 2. Test Agent Mode API

```bash
curl -X POST http://localhost:5000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"arm the drone\", \"mode\": \"agent\", \"telemetry\": {\"armed\": false, \"mode\": \"STABILIZE\"}}"
```

Expected response:
```json
{
  "reply": "Arming the drone now.",
  "command": {
    "type": "ARM",
    "params": {}
  }
}
```

### 3. Test Ask Mode API

```bash
curl -X POST http://localhost:5000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"what is my battery voltage?\", \"mode\": \"ask\", \"telemetry\": {\"battery\": 12.6, \"armed\": false}}"
```

Expected response:
```json
{
  "reply": "Your current battery voltage is 12.6 volts.",
  "command": null
}
```

### 4. Test Script Mode API

```bash
curl -X POST http://localhost:5000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"print hello world every 5 seconds\", \"mode\": \"script\"}"
```

Expected response:
```json
{
  "reply": "Here's your Lua script...",
  "script": "function update()\n  gcs:send_text(6, 'Hello World')\n  return update, 5000\nend\nreturn update()"
}
```

## MAVProxy Integration Testing

### Setup MAVProxy Module

```bash
# Find your MAVProxy modules directory
python -c "import MAVProxy; print(MAVProxy.__path__[0])"

# Copy module file
cp integrations/mavproxy/mavproxy_ai_backend.py <MAVProxy_path>/modules/
```

### Start SITL with MAVProxy

```bash
# Terminal 1: Start ArduPilot SITL
cd ~/ardupilot/ArduCopter
sim_vehicle.py --console --map

# Terminal 2: Start backend
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server
```

### Load AI Module in MAVProxy

```
MAVProxy> module load ai_backend
AI Backend module loaded
Backend URL: http://localhost:5000

MAVProxy> ai_backend status
Backend: Connected
Mode: agent (safe mode enabled)
```

### Test Commands

```
MAVProxy> arm throttle
Arming...
Throttle armed

MAVProxy> ai arm the drone
AI Backend: ARM command sent (already armed)

MAVProxy> ai take off to 10 meters
AI Backend: TAKEOFF to 10m sent

MAVProxy> ai what is my altitude?
AI Backend: You are currently at 10.2 meters above home position.

MAVProxy> ai land now
AI Backend: Mode LAND command sent

MAVProxy> disarm
Disarmed
```

## Mission Planner Integration Testing

### Option 1: Use Pre-built Fork

```bash
# Download latest release
# https://github.com/deepak61296/MissionPlanner/releases

# Extract and run MissionPlanner.exe
# No additional setup needed
```

### Option 2: Build from Source

```powershell
# Clone fork
git clone https://github.com/deepak61296/MissionPlanner.git
cd MissionPlanner
git checkout feature/script-mode-clean

# Open in Visual Studio 2022
# Build -> Build Solution
# Run -> Start Debugging (F5)
```

### Test Mission Planner Integration

1. **Start backend:**
```bash
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server
```

2. **Start SITL:**
```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py --console --map
```

3. **Connect Mission Planner:**
   - Open Mission Planner
   - Connection Type: UDP
   - Port: 14550
   - Click Connect

4. **Open AI Chat:**
   - Press `Ctrl+L` (or Tools -> AI Chat Assistant)
   - Backend URL should auto-detect: `http://localhost:5000`

5. **Test Agent Mode:**
   - Mode dropdown: `Agent`
   - Type: `arm the drone`
   - Should see: "ARM command sent"
   - Type: `take off to 10 meters`
   - Watch HUD altitude climb to 10m

6. **Test Ask Mode:**
   - Mode dropdown: `Ask`
   - Type: `what's my battery?`
   - Should see voltage response
   - Type: `how high am I flying?`
   - Should see altitude response

7. **Test Script Mode:**
   - Mode dropdown: `Script`
   - Type: `print battery voltage every 5 seconds`
   - Should generate Lua script
   - Click "Deploy" to flash to vehicle via MAVFTP

## Running Test Suite

### Full Comprehensive Test Suite

```bash
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend

# Make sure backend is running first
python -m backend.api_server

# In another terminal, run tests
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python tests/test_comprehensive.py
```

Or use batch script:
```bash
cd C:\Projects\ardupilot-ai-backend\scripts
run_comprehensive_tests.bat
```

Expected output:
```
========================================
ArduPilot AI Backend - Full Test Suite
150+ Tests with HTML Report
========================================

Backend running - starting comprehensive suite...
This will take ~8-12 minutes

Running tests...
✓ Agent mode tests (45/45)
✓ Ask mode tests (32/32)
✓ Script mode tests (28/28)
✓ Command extraction tests (35/35)
✓ Safety validation tests (11/11)

Total: 151 passed, 0 failed
Report: tests/test_report.html
```

### Quick Unit Tests

```bash
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
pytest tests/ -v
```

### Specific Test Categories

```bash
# Test only command extraction
pytest tests/test_comprehensive.py::TestCommandExtraction -v

# Test only Agent mode
pytest tests/test_comprehensive.py::TestAgentMode -v

# Test only Script mode
pytest tests/test_comprehensive.py::TestScriptMode -v

# Test only safety validation
pytest tests/test_comprehensive.py::TestSafetyValidation -v
```

## Troubleshooting Commands

### Check Ollama Service

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# List installed models
ollama list

# Test model inference
ollama run qwen2.5-coder:3b "Hello, are you working?"

# Pull model if missing
ollama pull qwen2.5-coder:3b
```

### Check Backend Logs

```bash
# If backend crashes, check logs
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server --debug

# Or check for specific errors
python -m backend.api_server 2>&1 | grep ERROR
```

### Check Python Dependencies

```bash
conda activate ardupilot_ai
pip list | grep -E "flask|requests|ollama|sentence-transformers"

# Expected output:
# Flask                     2.3.0
# requests                  2.31.0
# sentence-transformers     2.2.2
```

### Reset Everything

If nothing works, nuclear option:

```bash
# Stop all services
# Close MAVProxy, Mission Planner, backend terminals

# Remove conda environment
conda env remove -n ardupilot_ai
conda env remove -n ai_backend

# Recreate environment
conda create -n ardupilot_ai python=3.10 -y
conda activate ardupilot_ai

# Reinstall dependencies
cd C:\Projects\ardupilot-ai-backend
pip install -r requirements.txt

# Restart Ollama service (Windows)
# Open Task Manager -> Find "ollama" -> End Task
# Then: ollama serve

# Restart backend
python -m backend.api_server
```

## Environment Variables (Optional)

Create a `.env` file in project root for custom settings:

```bash
# .env file
OLLAMA_HOST=http://localhost:11434
API_PORT=5000
DEFAULT_MODEL=qwen2.5-coder:3b
SCRIPT_MODEL=qwen2.5-coder:7b
LOG_LEVEL=INFO
```

Load with:
```bash
conda activate ardupilot_ai
export $(cat .env | xargs)  # Linux/macOS
# Or manually set on Windows via System Properties
python -m backend.api_server
```

## Performance Optimization

### GPU Acceleration (NVIDIA only)

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# If True, backend will auto-use GPU
# If False, install CUDA toolkit:
# https://developer.nvidia.com/cuda-downloads

# Verify GPU usage while backend is running
nvidia-smi
```

### Model Size Selection

For faster responses on limited hardware:

```bash
# Install smaller models
ollama pull qwen2.5:1.5b
ollama pull qwen2.5-coder:1.5b

# Edit backend/config.py
# DEFAULT_MODEL = "qwen2.5:1.5b"
# SCRIPT_MODEL = "qwen2.5-coder:3b"  # Use 3B instead of 7B

# Restart backend
python -m backend.api_server
```

## Summary of Key Commands

```bash
# Initial setup
ollama pull qwen2.5-coder:3b qwen2.5-coder:7b
conda create -n ardupilot_ai python=3.10 -y
conda activate ardupilot_ai
pip install -r requirements.txt

# Start backend
python -m backend.api_server

# Verify
curl http://localhost:5000/health

# Run tests
python tests/test_comprehensive.py

# MAVProxy
module load ai_backend
ai arm the drone

# Mission Planner
# Press Ctrl+L, type commands
```
