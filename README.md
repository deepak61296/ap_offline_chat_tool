# ArduPilot AI Chat - Offline Backend

AI-powered chat assistant for ArduPilot drones using local LLM (no internet required).

## ⚠️ Warnings

- **SITL only** - Not tested on real hardware
- **Copter only** - Plane/Rover not supported yet
- **No warranty** - Use at your own risk (GPL-3.0)

## 📦 Mission Planner Integration

**Download Mission Planner with AI Chat:**
https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend

Extract and run `MissionPlanner.exe`, then press **Ctrl+L** for AI Chat.

## 🚀 Quick Start

### 1. Install Ollama

Download and install: https://ollama.com/download

After installation, open terminal and pull the model:
```bash
ollama pull qwen2.5:3b
```

### 2. Clone and Setup

```bash
git clone https://github.com/deepak61296/ap_offline_chat_tool.git
cd ap_offline_chat_tool

# Windows
conda create -n ardupilot_ai python=3.10 -y
conda activate ardupilot_ai
pip install -r requirements.txt
```

### 3. Start Backend

```bash
# Windows - Start Ollama first
ollama serve

# In another terminal
cd ap_offline_chat_tool
conda activate ardupilot_ai
python -m backend.api_server
```

Backend runs at: http://localhost:5000

### 4. Use with Mission Planner

1. Download Mission Planner: https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend
2. Run `MissionPlanner.exe`
3. Press **Ctrl+L** to open AI Chat
4. Connect to SITL or simulator
5. Chat with your drone!

## 💬 Example Commands

**Agent Mode** (sends commands):
- "arm the drone and take off to 10 meters"
- "move forward 5 meters"
- "land now"

**Ask Mode** (queries telemetry):
- "what's my battery level?"
- "how high am I flying?"
- "what mode am I in?"

## 🧪 Testing

**Current accuracy:** 78.8% on 151 rigorous test cases

Run tests:
```bash
cd tests
run_comprehensive_tests.bat
```

See `tests/README_TESTS.md` for details.

## 📋 Requirements

- Windows 10/11
- 8GB RAM minimum
- GPU recommended (works on CPU too)
- Ollama installed
- Python 3.10+

## 🔗 Links

- **Mission Planner Fork:** https://github.com/deepak61296/MissionPlanner
- **Latest Release:** https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend
- **Report Issues:** https://github.com/deepak61296/ap_offline_chat_tool/issues

## 📄 License

GPL-3.0 (for ArduPilot compatibility)

**NO WARRANTY - Use at your own risk. This is experimental software.**
