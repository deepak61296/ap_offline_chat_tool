# ArduPilot AI Chat - Offline Backend

AI-powered chat assistant for ArduPilot drones using local LLM (runs offline, no internet required).

## What is This?

This backend enables natural language interaction with your ArduPilot drone through a local AI model. It processes voice-like commands and queries without requiring an internet connection.

**Example conversations:**
- "arm and take off to 10 meters" → Sends ARM + TAKEOFF commands
- "what's my altitude?" → Queries telemetry and responds
- "move forward 5 meters" → Sends movement command

## 🎥 Demo Video

[Watch Demo Video](https://github.com/deepak61296/ardupilot-ai-backend/raw/main/demo.mkv) (16 MB .mkv file)

## 📦 Quick Start - Mission Planner Integration

**Download Mission Planner with AI Chat:**  
https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend

1. Extract ZIP and run `MissionPlanner.exe`
2. Follow backend setup below
3. Press **Ctrl+L** to open AI Chat
4. Connect to SITL and start chatting!

## 🚀 Backend Setup

### Prerequisites

- **Windows 10/11** (64-bit)
- **8GB RAM minimum** (16GB recommended)
- **GPU recommended** (NVIDIA preferred, works on CPU too)
- **Python 3.10 or 3.11** (not 3.12+)

### Step 1: Install Miniconda

Download and install Miniconda:  
https://docs.anaconda.com/miniconda/

During installation:
- ✅ Check "Add Miniconda to PATH"
- ✅ Use all default options

After installation, open a **new terminal** to verify:
```bash
conda --version
# Should show: conda 24.x.x or similar
```

### Step 2: Install Ollama

Download and install Ollama:  
https://ollama.com/download

After installation, pull the AI model:
```bash
ollama pull qwen2.5:3b
```

This downloads a 2GB model (one-time download).

### Step 3: Clone Repository

```bash
git clone https://github.com/deepak61296/ardupilot-ai-backend.git
cd ardupilot-ai-backend
```

### Step 4: Create Conda Environment

```bash
# Create environment with Python 3.10
conda create -n ai_backend python=3.10 -y

# Activate environment
conda activate ai_backend
```

**Note:** You'll need to activate this environment every time you start the backend.

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, requests, and other required packages.

### Step 6: Start Backend

**Terminal 1 - Start Ollama:**
```bash
ollama serve
```
Leave this running.

**Terminal 2 - Start Backend:**
```bash
conda activate ai_backend
cd ardupilot-ai-backend
python -m backend.api_server
```

Backend runs at: **http://localhost:5000**

You should see:
```
INFO:werkzeug: * Running on http://127.0.0.1:5000
Backend ready!
```

## 📁 Project Structure

```
ardupilot-ai-backend/
├── backend/
│   ├── api_server.py      # Flask server (handles requests from GCS)
│   ├── commands.py        # Command extraction and parsing
│   ├── prompts.py         # AI prompts for Agent/Ask/Script modes
│   ├── config.py          # Configuration (model, API settings)
│   └── ...
├── integrations/
│   ├── mavproxy/          # MAVProxy module + install docs
│   └── mission_planner/   # Mission Planner plugin files
├── tests/
│   ├── test_comprehensive.py    # Main test suite (151 tests)
│   └── README_TESTS.md          # Test documentation
├── ARCHITECTURE.md        # System architecture docs
├── COMPATIBILITY.md       # Version compatibility matrix
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and data flow
- **[COMPATIBILITY.md](COMPATIBILITY.md)** - Version compatibility and installation
- **[integrations/mavproxy/](integrations/mavproxy/)** - MAVProxy module docs
- **[integrations/mission_planner/](integrations/mission_planner/)** - Mission Planner plugin docs

## 🔧 How It Works

### Architecture

```
Mission Planner (Ctrl+L) 
    ↓ HTTP Request
Backend API Server (:5000)
    ↓ Process message
LLM (Ollama - qwen2.5:3b)
    ↓ Generate response
Command Parser
    ↓ Extract commands
Mission Planner (Execute)
```

### Two Modes

**1. Agent Mode** (sends commands to drone)
- Input: "take off to 10 meters"
- LLM generates: "TAKEOFF altitude=10"
- Backend extracts: `TAKEOFF 10`
- Mission Planner executes command

**2. Ask Mode** (queries telemetry)
- Input: "what's my battery?"
- Mission Planner sends current telemetry
- LLM analyzes and responds: "Battery at 12.4V (87%)"
- No commands sent

### Command Extraction

The backend uses regex patterns to extract commands from LLM responses:
- `ARM` / `DISARM`
- `TAKEOFF altitude=X`
- `LAND`
- `GOTO lat,lon,alt`
- `MOVE_DIRECTION direction distance`
- And more...

See `backend/commands.py` for full list.

## 💬 Usage Examples

### Agent Mode (Command Execution)

| You Say | Drone Does |
|---------|-----------|
| "arm the drone" | Arms motors |
| "take off to 15 meters" | Takes off to 15m |
| "move forward 10 meters" | Moves forward 10m |
| "set param disarm_delay to 50" | Sets DISARM_DELAY parameter to 50 |
| "fly to home" | Returns to launch point |
| "land now" | Lands at current position |
| "disarm" | Disarms motors |

### Ask Mode (Telemetry Queries)

| You Ask | Response |
|---------|----------|
| "what's my battery?" | "Battery at 12.4V (87%)" |
| "how high am I?" | "Current altitude: 25.3 meters" |
| "what mode am I in?" | "You're in GUIDED mode" |
| "how fast am I going?" | "Ground speed: 3.2 m/s" |

## 🧪 Testing

Current test accuracy: **78.8%** on 151 rigorous test cases

Run the test suite:
```bash
cd tests
run_comprehensive_tests.bat
```

This opens an HTML report showing passed/failed tests.

**Test categories:**
- Basic flight commands (ARM, TAKEOFF, LAND)
- Movement commands (GOTO, MOVE_DIRECTION)
- Altitude commands
- Safety scenarios (rejecting dangerous requests)
- Natural language variations
- Typo tolerance

See `tests/README_TESTS.md` for details.

## 🔍 Troubleshooting

### "Backend not available" in Mission Planner

**Check:**
1. Is Ollama running? (`ollama serve` in terminal)
2. Is backend running? (`python -m backend.api_server`)
3. Is conda environment activated? (`conda activate ai_backend`)
4. Backend should show "Running on http://127.0.0.1:5000"

**Test manually:**
```bash
curl http://localhost:5000/health
# Should return: {"status": "ok", "model": "qwen2.5:3b"}
```

### "ollama: command not found"

Ollama wasn't added to PATH. Fix:
1. Reinstall Ollama
2. Restart terminal
3. Try: `where ollama` (should show path)

### "conda: command not found"

Miniconda wasn't added to PATH. Fix:
1. Reinstall Miniconda
2. Check "Add to PATH" option
3. Restart terminal

### Backend starts but no response

**Model not downloaded:**
```bash
ollama pull qwen2.5:3b
```

**Wrong model name in config:**
Check `backend/config.py` - MODEL should be "qwen2.5:3b"

### Commands not executing

**Check console output** in backend terminal:
- Look for errors in command extraction
- Check if LLM response format is correct

**Enable debug logging:**
Edit `backend/api_server.py` and set `debug=True` in `app.run()`

### Slow responses

**CPU mode is slower than GPU** (4-10 seconds per response depending on processor). Solutions:
- Use GPU if available (NVIDIA recommended)
- Use smaller model: `ollama pull qwen2.5:1.5b`
- Reduce conversation history in config

### Module import errors

**Wrong directory or environment:**
```bash
# Make sure you're in the right folder
cd ardupilot-ai-backend

# Make sure environment is activated
conda activate ai_backend

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port 5000 already in use

**Change port in two places:**

1. `backend/config.py`: Change `API_PORT = 5000` to `API_PORT = 5001`
2. Mission Planner AI settings: Change backend URL to `http://localhost:5001`

## 🛠️ Development

### Running in CPU-only mode

```bash
scripts\start_backend_cpu.bat
```

This works but is slower (4-10 seconds per response depending on your processor).

### Using different models

Edit `backend/config.py`:
```python
MODEL = "qwen2.5:1.5b"  # Smaller, faster
# or
MODEL = "qwen2.5:7b"    # Larger, more accurate (requires more RAM)
```

Then pull the model:
```bash
ollama pull qwen2.5:1.5b
```

### Adding new commands

1. Add pattern to `backend/commands.py`
2. Add examples to test suite
3. Update `backend/prompts.py` if needed

## 📋 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| RAM | 8GB | 16GB |
| GPU | None (CPU works) | NVIDIA GPU |
| Storage | 5GB | 10GB |
| Python | 3.10 | 3.10 or 3.11 |

## 🔗 Links

- **Mission Planner Fork:** https://github.com/deepak61296/MissionPlanner
- **Latest Release:** https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend
- **Report Issues:** https://github.com/deepak61296/ardupilot-ai-backend/issues
- **Ollama:** https://ollama.com
- **Miniconda:** https://docs.anaconda.com/miniconda/

## ⚠️ Important Notes

- **Testing:** Currently tested on SITL only - not tested on real hardware
- **Vehicle Support:** Copter only (Plane/Rover support coming soon)
- **License:** GPL-3.0 (for ArduPilot compatibility)

Use responsibly and always test in simulation first.
