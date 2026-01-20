# ArduPilot AI Backend

Control your ArduPilot drone with natural language. Talk to your drone like a co-pilot.

> **⚠️ IMPORTANT:** This software is provided "as is" under GPL-3.0 license with **absolutely no warranty**. Currently tested **only on SITL** (Software In The Loop simulation), **not real hardware**. Use at your own risk.

## What You Need

**This backend requires the compatible Mission Planner fork:**
- Mission Planner Fork: https://github.com/deepak61296/MissionPlanner

**This Mission Planner fork requires this backend:**
- AI Backend: https://github.com/deepak61296/ArduPilot-AI-Backend

Both must be installed and running together.

## Requirements

- **Windows 10/11** (Linux support coming soon)
- **GPU:** NVIDIA GPU recommended (works on CPU too)
- **Vehicle:** Copter only (Plane/Rover coming soon)

## Quick Setup

### 1. Install Ollama

Download and install: https://ollama.com

**Start Ollama service:**
```cmd
ollama serve
```

Then pull the model (in a new terminal):
```cmd
ollama pull qwen2.5:3b
```

### 2. Install Miniconda (if needed)

**Check if you have conda:**
```cmd
conda --version
```

**If not installed:**
1. Download: https://docs.conda.io/en/latest/miniconda.html
2. Run installer (Miniconda3-latest-Windows-x86_64.exe)
3. Restart terminal

### 3. Setup AI Backend

```cmd
# Clone repo
git clone https://github.com/deepak61296/ArduPilot-AI-Backend.git
cd ArduPilot-AI-Backend\ap_offline_chat_tool

# Create environment
conda create -n ap_chat_tools python=3.10 -y
conda activate ap_chat_tools

# Install dependencies
pip install -r backend\requirements.txt

# Start backend
scripts\start_backend.bat
```

Backend runs on `http://localhost:5000`

### 4. Get Mission Planner

**Option A: Download .exe (Recommended)**

Download from: https://github.com/deepak61296/MissionPlanner/releases

**Option B: Build from Source**

```cmd
git clone https://github.com/deepak61296/MissionPlanner.git
# Follow build instructions in Mission Planner repo
```

### 5. Use AI Chat

1. Make sure backend is running (step 3)
2. Open Mission Planner
3. Press **Ctrl+L** to open AI Chat
4. Start chatting!

## Usage

### Agent Mode - Control Drone
```
"arm the drone"
"takeoff to 15 meters"
"move north 20 meters"
"increase altitude by 10m"
"change mode to loiter"
"land"
```

### Ask Mode - Get Telemetry & Info
```
"what's my battery status?"
"what is my current altitude?"
"show me yaw heading"
"what's my roll and pitch?"
"where am I?"
```

## Test Results

**Accuracy:** 76.8% (116/151 tests passing)  
**Model:** qwen2.5:3b (3B parameters, 2GB)  
**Note:** Excellent for a small local model running offline!

See `tests/test_report.html` for detailed results.

## Troubleshooting

**Backend won't start?**
```cmd
# 1. Make sure Ollama is running
ollama serve

# 2. Check model is downloaded (in new terminal)
ollama list

# 3. Activate conda environment
conda activate ap_chat_tools

# 4. Pull model if missing
ollama pull qwen2.5:3b
```

**Mission Planner can't connect?**
- Backend must be running on port 5000
- Look for "AI Backend connected ✓" in chat window
- Check firewall isn't blocking localhost:5000

**Commands not working?**
- Use **Agent mode** (not Ask mode) for commands
- Use direct commands: "arm the drone" ✓
- Don't ask questions: "can you arm?" ✗

## Project Structure

```
ap_offline_chat_tool/
├── backend/
│   ├── api_server.py       # HTTP API server
│   ├── commands.py         # Command extraction
│   ├── prompts.py          # AI prompts
│   ├── config.py           # Configuration
│   └── telemetry_data.py   # Telemetry formatting
├── scripts/
│   ├── start_backend.bat           # Main startup
│   ├── start_backend_cpu.bat       # CPU-only mode
│   └── start_backend_lowpower.bat  # Low-power mode
├── tests/
│   ├── test_comprehensive.py   # 170+ tests
│   └── test_report.html        # Latest results
└── docs/                       # Documentation
```

## Running Tests

```cmd
# Activate environment
conda activate ap_chat_tools

# Run tests
scripts\run_comprehensive_tests.bat

# View results
# Open tests\test_report.html in browser
```

## What's Supported

- **Vehicle:** Copter only
- **OS:** Windows only
- **Testing:** SITL only (not tested on real hardware)
- **Commands:** ARM, DISARM, TAKEOFF, LAND, RTL, movement, altitude, mode changes

## Roadmap

- [ ] Real hardware testing
- [ ] Plane and Rover support
- [ ] Linux support
- [ ] Fine-tuned model (90%+ accuracy)
- [ ] Waypoint and mission commands
- [ ] QGroundControl integration

## License

**GPL-3.0** - See LICENSE file

This project is licensed under GPL-3 to maintain compatibility with ArduPilot.

**NO WARRANTY:** This software comes with absolutely no warranty. Use at your own risk.

## Links

- **Mission Planner Fork:** https://github.com/deepak61296/MissionPlanner
- **ArduPilot:** https://ardupilot.org
- **Ollama:** https://ollama.com
- **Issues:** https://github.com/deepak61296/ArduPilot-AI-Backend/issues

---

**Made for the ArduPilot community**
