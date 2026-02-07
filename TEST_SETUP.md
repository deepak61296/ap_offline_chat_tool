# Setup and Test Commands

## 1. Conda Environment Setup

```bash
# Install Ollama models
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b

# Verify models
ollama list

# Create conda environment
conda create -n ardupilot_ai python=3.10 -y

# Activate environment
conda activate ardupilot_ai

# Install dependencies
cd C:\Projects\ardupilot-ai-backend
pip install -r requirements.txt

# Verify installation
python -c "import flask; import requests; print('Dependencies OK')"
```

## 2. Start Backend

```bash
# Terminal 1: Start Ollama (if not running)
ollama serve

# Terminal 2: Start backend
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server

# Terminal 3: Verify backend is running
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "ok",
  "model": "qwen2.5-coder:3b"
}
```

## 3. MAVProxy Test Commands

### Setup MAVProxy Module

```bash
# Find MAVProxy modules directory
python -c "import MAVProxy; print(MAVProxy.__path__[0])"

# Copy module to MAVProxy
cp integrations/mavproxy/mavproxy_ai_backend.py <MAVProxy_path>/modules/
```

### Start SITL and MAVProxy

```bash
# Terminal 1: Start ArduPilot SITL
cd ~/ardupilot/ArduCopter
sim_vehicle.py --console --map

# Terminal 2: Start backend (if not running)
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server
```

### Test in MAVProxy Console

```
# Load AI module
module load ai_backend

# Check status
ai_backend status

# Enable AI mode
ai_backend enable

# Test commands
arm throttle
ai take off to 10 meters
ai what's my altitude?
ai land
disarm
```

Expected outputs:
- `ai_backend status` → "Backend: Connected, Mode: agent (safe mode enabled)"
- `ai take off to 10 meters` → "AI Backend: TAKEOFF to 10m sent"
- `ai what's my altitude?` → AI responds with current altitude
- `ai land` → "AI Backend: Mode LAND command sent"

## 4. Mission Planner Test Commands

### Start SITL for Mission Planner

```bash
# Terminal 1: Start SITL
cd ~/ardupilot/ArduCopter
sim_vehicle.py --console --map

# Terminal 2: Start backend
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend
python -m backend.api_server
```

### Test in Mission Planner

1. **Connect to SITL**
   - Connection Type: UDP
   - Port: 14550
   - Click "Connect"

2. **Open AI Chat**
   - Press `Ctrl+L`
   - Backend URL should show: `http://localhost:5000`

3. **Test Agent Mode**
   - Mode dropdown: `Agent`
   - Type: `arm the drone`
   - Expected: "ARM command sent"
   - Type: `take off to 10 meters`
   - Expected: Altitude climbs to 10m on HUD
   - Type: `land`
   - Expected: Vehicle lands

4. **Test Ask Mode**
   - Mode dropdown: `Ask`
   - Type: `what's my battery?`
   - Expected: Voltage response
   - Type: `how high am I?`
   - Expected: Altitude response

5. **Test Script Mode**
   - Mode dropdown: `Script`
   - Type: `print battery voltage every 5 seconds`
   - Expected: Lua script generated
   - (Optional) Click "Deploy" to flash via MAVFTP

## 5. Full Test Suite

```bash
# Make sure backend is running
conda activate ardupilot_ai
cd C:\Projects\ardupilot-ai-backend

# Run comprehensive tests
python tests/test_comprehensive.py

# Or use batch script (Windows)
cd scripts
run_comprehensive_tests.bat
```

Expected: 151 tests, majority passing (100+ passing is good)

## 6. Quick API Tests

```bash
# Test Agent mode
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"arm the drone\", \"mode\": \"agent\", \"telemetry\": {\"armed\": false}}"

# Expected response:
# {"reply": "Arming the drone now.", "command": {"type": "ARM", "params": {}}}

# Test Ask mode
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"what is my battery?\", \"mode\": \"ask\", \"telemetry\": {\"battery\": 12.6}}"

# Expected response with battery info

# Test Script mode
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"print hello every 5 seconds\", \"mode\": \"script\"}"

# Expected response with Lua script
```

## Troubleshooting

### Backend won't start
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check models are downloaded
ollama list

# Reinstall dependencies
conda activate ardupilot_ai
pip install -r requirements.txt --force-reinstall
```

### MAVProxy module not loading
```bash
# Check module exists
ls <MAVProxy_path>/modules/mavproxy_ai_backend.py

# Check MAVProxy version
mavproxy.py --version

# Try loading with full path
module load mavproxy_ai_backend
```

### Backend not responding
```bash
# Check if backend is actually running
curl http://localhost:5000/health

# Check port 5000 is not in use
netstat -an | grep 5000

# Restart backend
# Ctrl+C to stop
python -m backend.api_server
```
