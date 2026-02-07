# ArduPilot AI Backend

AI-powered natural language drone control using local LLMs. Runs fully offline.

Talk to your drone in plain English through MAVProxy or Mission Planner.

**Examples:**
```
arm the drone
takeoff to 10 meters
move north 20 meters
set speed to 5 m/s
what's my battery?
land
```

## Demo

**MAVProxy:** [Watch Demo](demos/mavproxy_demo.mkv)
**Mission Planner:** [Watch Demo](demos/mission_planner_demo.mkv)

## How It Works

```
User (natural language)
    |
    v
GCS (MAVProxy / Mission Planner)
    |  HTTP POST /chat
    v
Backend Server (Flask)
    |
    v
Local LLM (Ollama)
    |
    v
Command Extraction (regex)
    |
    v
GCS executes via MAVLink
```

Three modes:
- **Agent** - Execute commands (arm, takeoff, land, move, etc.)
- **Ask** - Read-only telemetry queries
- **Script** - Generate Lua scripts for the flight controller

---

## Quick Start

### 1. Backend Setup

**Prerequisites:** Python 3.10+, 8GB RAM min

```bash
# Install Ollama (https://ollama.com/download)
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b

# Clone and setup
git clone https://github.com/deepak61296/ardupilot-ai-backend.git
cd ardupilot-ai-backend

# Create environment
conda create -n ardupilot_ai python=3.10 -y
conda activate ardupilot_ai
pip install -r requirements.txt

# Start backend
ollama serve                     # Terminal 1
python -m backend.api_server     # Terminal 2
```

Backend runs at **http://localhost:5000**

### 2. Connect a GCS

Choose **one** of these:

---

## GCS Integration: Mission Planner

### Option A: Download Pre-built (Easiest)

1. Download from [Mission Planner releases](https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend)
2. Extract and run `MissionPlanner.exe`
3. Connect to vehicle (SITL or real)
4. Press **Ctrl+L** to open AI Chat
5. Start typing commands

### Option B: Build from Fork

```bash
git clone https://github.com/deepak61296/MissionPlanner.git
cd MissionPlanner
git checkout feature/script-mode-clean
dotnet build MissionPlanner.csproj
```

### Option C: Apply to Your Own MP Build (Advanced)

Copy integration files from `integrations/mission_planner/` to your MP source:

```
integrations/mission_planner/ChatAssistant.cs         -> GCSViews/ChatAssistant.cs
integrations/mission_planner/GCSViews/ChatAssistant.Designer.cs -> GCSViews/ChatAssistant.Designer.cs
integrations/mission_planner/GCSViews/FlightData.cs   -> GCSViews/FlightData.cs
integrations/mission_planner/GCSViews/ConfigurationView/ConfigRawParams.cs -> GCSViews/ConfigurationView/ConfigRawParams.cs
integrations/mission_planner/AIBackendService.cs      -> AIBackendService.cs
integrations/mission_planner/DroneCommandExecutor.cs  -> DroneCommandExecutor.cs
```

Then apply the build fix:
```bash
git apply integrations/mission_planner/csproj.patch
dotnet build MissionPlanner.csproj
```

### Configure Backend URL

Right-click the connection button in Mission Planner to set backend URL (default: `http://localhost:5000`).

---

## GCS Integration: MAVProxy

### Option A: Use Our Fork (Recommended)

```bash
git clone https://github.com/deepak61296/MAVProxy.git
cd MAVProxy
git checkout feature/ai-backend-integration
pip install -e .
```

Start MAVProxy:
```bash
mavproxy.py --master=udp:127.0.0.1:14550 --console
```

Then enable the AI module:
```
module load ai_backend
ai_backend enable
```

Now type natural language directly:
```
arm the drone
takeoff to 15 meters
move north 30 meters
change mode to loiter
```

### Option B: Drop Module into Existing MAVProxy

Copy the module file from `integrations/mavproxy/`:

**Windows:**
```bash
copy integrations\mavproxy\mavproxy_ai_backend.py %USERPROFILE%\AppData\Local\MAVProxy\modules\
```

**Linux/Mac:**
```bash
cp integrations/mavproxy/mavproxy_ai_backend.py ~/.local/lib/python3.*/site-packages/MAVProxy/modules/
```

Then load in MAVProxy:
```
module load ai_backend
ai_backend enable
```

### Optional: --ai-backend Flag

Apply the patch for auto-loading on startup:
```bash
cd /path/to/MAVProxy
git apply /path/to/integrations/mavproxy/mavproxy_ai_flag.patch
```

Then start with:
```bash
mavproxy.py --master=udp:127.0.0.1:14550 --console --ai-backend
```

### MAVProxy Commands

```
ai_backend enable      # Enable natural language
ai_backend disable     # Disable
ai_backend status      # Show connection status
ai_backend safe        # Enable y/n confirmation
ai_backend unsafe      # Disable confirmations
```

Backend URL auto-connects to http://localhost:5000

---

## Verification

### Step 1: Check Backend Health

```bash
curl http://localhost:5000/health
```

Expected:
```json
{"status": "ok", "model": "qwen2.5-coder:3b"}
```

### Step 2: Test Chat API Directly

```bash
curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d "{\"message\": \"hello\", \"mode\": \"agent\"}"
```

Expected: JSON response with `"success": true` and a greeting.

### Step 3: Test Command Extraction

```bash
curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d "{\"message\": \"arm the drone\", \"mode\": \"agent\"}"
```

Expected: Response with `"command": {"type": "ARM", ...}`

### Step 4: Test with MAVProxy + SITL

**Terminal 1 - Start SITL:**
```bash
cd ArduCopter
sim_vehicle.py --console --map
```

**Terminal 2 - Start MAVProxy with AI:**
```bash
mavproxy.py --master=udp:127.0.0.1:14550 --console
module load ai_backend
ai_backend enable
ai_backend status
```

Expected: `Backend: Connected`

**Test commands:**
```
arm the drone
# -> "AI Backend: ARM command sent"

takeoff to 10 meters
# -> "AI Backend: TAKEOFF to 10m sent"

move north 20 meters
# -> "AI Backend: Moving north 20m"

what is my altitude?
# -> AI responds with current altitude

land
# -> "AI Backend: Mode LAND command sent"
```

### Step 5: Test with Mission Planner

1. Start SITL: `sim_vehicle.py --console --map`
2. Open Mission Planner, connect to `udp:127.0.0.1:14550`
3. Press **Ctrl+L** to open AI Chat
4. Type: `arm the drone` -> Should arm
5. Type: `takeoff to 10 meters` -> Should take off
6. Switch to **Ask Mode** and type: `what's my battery?` -> Should show voltage
7. Switch to **Script Mode** and type: `print battery voltage every 5 seconds` -> Should generate Lua script

---

## Running Tests

### Full Test Suite (151 tests)

```bash
conda activate ardupilot_ai
cd ardupilot-ai-backend
python -m pytest tests/test_comprehensive.py -v
```

Or use the batch script:
```bash
cd tests
run_comprehensive_tests.bat
```

### Quick Backend Smoke Test

```bash
# Health check
curl http://localhost:5000/health

# Test endpoint
curl http://localhost:5000/test

# List models
curl http://localhost:5000/models
```

### Test Categories

| Category | What It Tests |
|----------|--------------|
| Flight commands | ARM, DISARM, TAKEOFF, LAND, RTL |
| Movement | GOTO, MOVE north/south/east/west |
| Altitude | Increase/decrease altitude mid-flight |
| Speed/Yaw | SET_SPEED, SET_YAW/heading |
| Parameters | GET_PARAM, SET_PARAM |
| Mode changes | GUIDED, AUTO, LOITER, STABILIZE, etc. |
| Safety | Rejecting dangerous/ambiguous requests |
| Ask mode | Telemetry queries without execution |
| Script mode | Lua script generation and validation |
| Edge cases | Typos, casual language, missing params |

---

## Supported Commands

| Command | Example | What Happens |
|---------|---------|-------------|
| ARM | "arm the drone" | Arms motors |
| DISARM | "disarm" | Disarms motors |
| TAKEOFF | "takeoff to 15m" | Takes off to altitude |
| LAND | "land now" | Lands at current position |
| RTL | "return home" | Returns to launch |
| CHANGE_MODE | "switch to loiter" | Changes flight mode |
| MOVE_DIRECTION | "move north 20m" | Moves in cardinal direction |
| ALTITUDE_CHANGE | "go up 10 meters" | Changes altitude mid-flight |
| SET_SPEED | "set speed to 5 m/s" | Changes ground speed |
| SET_YAW | "face east" | Changes heading |
| GOTO | "fly to 37.77, -122.41" | Goes to coordinates |
| GET_PARAM | "what is BATT_CAPACITY?" | Reads parameter |
| SET_PARAM | "set disarm_delay to 40" | Sets parameter |
| REBOOT | "reboot" | Reboots flight controller |

---

## Project Structure

```
ardupilot-ai-backend/
├── backend/                       # Core backend server
│   ├── api_server.py              # Flask HTTP API
│   ├── commands.py                # Command extraction
│   ├── prompts.py                 # AI system prompts
│   ├── config.py                  # Settings and limits
│   ├── telemetry_data.py          # Telemetry formatting
│   ├── template_injector_v2.py    # Lua template library
│   ├── lua_postprocessor.py       # Lua script fixes
│   └── mavlink_manager.py         # Standalone MAVLink (optional)
├── integrations/
│   ├── mavproxy/                  # MAVProxy module (2 files)
│   └── mission_planner/           # Mission Planner plugin (8 files)
├── tests/
│   ├── test_comprehensive.py      # 151 test cases
│   └── test_model_comparison.py   # Model benchmarks
├── ARCHITECTURE.md                # System design
├── COMPATIBILITY.md               # Version matrix
├── CONTRIBUTING.md                # Developer guide
└── requirements.txt
```

## Project Structure

- **[integrations/mavproxy/](integrations/mavproxy/)** - MAVProxy module
- **[integrations/mission_planner/](integrations/mission_planner/)** - Mission Planner plugin files

---

## Troubleshooting

### Backend won't start
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check model is downloaded
ollama list

# Check Python environment
conda activate ardupilot_ai
pip install -r requirements.txt --force-reinstall
```

### Commands not executing
- Check backend terminal for errors
- Verify backend is connected: `curl http://localhost:5000/health`
- In MAVProxy: `ai_backend status` should show `Backend: Connected`

### Slow responses
- GPU mode is much faster than CPU
- Try smaller model: `ollama pull qwen2.5-coder:1.5b`
- Edit `backend/config.py` to change `DEFAULT_MODEL`

### Port 5000 in use
- Change in `backend/config.py`: `API_PORT = 5001`
- Update GCS backend URL to `http://localhost:5001`

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| RAM | 8GB | 16GB |
| GPU | None (CPU works) | NVIDIA GPU |
| Storage | 5GB | 10GB |
| Python | 3.10 | 3.10 or 3.11 |

## Documentation

- **[Project Overview](docs/PROJECT_OVERVIEW.md)** - Features, use cases, and detailed introduction
- **[Architecture](docs/ARCHITECTURE.md)** - System design and technical deep-dive
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Developer workflow and coding standards
- **[Compatibility Matrix](docs/COMPATIBILITY.md)** - Version requirements
- **[Full Documentation Index](docs/README.md)** - All documentation

## Links

- **MAVProxy Fork:** https://github.com/deepak61296/MAVProxy
- **Mission Planner Fork:** https://github.com/deepak61296/MissionPlanner
- **MP Release:** https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend
- **Issues:** https://github.com/deepak61296/ardupilot-ai-backend/issues
- **Ollama:** https://ollama.com
- **ArduPilot SITL:** https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html

## Notes

- Tested on SITL and real hardware
- Supports ArduCopter
- License: GPL-3.0

Always test in simulation first.
