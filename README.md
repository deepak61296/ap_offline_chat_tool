# ArduPilot AI Backend

Natural language drone control with structured tool calling. Talk to your drone through QGroundControl, MAVProxy, or Mission Planner. Runs fully offline with [Ollama](https://ollama.com).

**v3.0** — Planner → Executor pipeline with JSON tool calling. See `tests/README_TESTS.md` for the current benchmark summary.

```
arm the drone and takeoff to 25m
move forward 10m then right 20m then circle 8m radius
set speed to 5 m/s
what is BATT_CAPACITY?
bring it back its dangerous
```

## Demos

**Mission Planner**

[![Mission Planner Demo](https://img.youtube.com/vi/mMeY41tOgTs/0.jpg)](https://www.youtube.com/watch?v=mMeY41tOgTs)

**QGroundControl**

[![QGroundControl Demo](https://img.youtube.com/vi/J89E-0sYJxw/0.jpg)](https://www.youtube.com/watch?v=J89E-0sYJxw)

**MAVProxy**

[![MAVProxy Demo](https://img.youtube.com/vi/8ATi4Uj1ndc/0.jpg)](https://www.youtube.com/watch?v=8ATi4Uj1ndc)

## Quick Start

**Prerequisites:** Python 3.10+, 8GB RAM, [Ollama](https://ollama.com/download)

```bash
# Pull the default model
ollama pull qwen2.5:3b

# Clone and install
git clone https://github.com/deepak61296/ardupilot-ai-backend.git
cd ardupilot-ai-backend
pip install -r requirements.txt

# Start the backend (make sure ollama is running first)
python run_server.py
```

Backend runs at `http://localhost:5000`. If you prefer **conda**:

```bash
conda create -n ardupilot_ai python=3.10 -y
conda activate ardupilot_ai
pip install -r requirements.txt
python run_server.py
```

**Windows users** can use the batch file instead:
```
start_backend.bat
```

## GCS Setup

Pick your ground control station below. You need the backend running first (see Quick Start above).

### Mission Planner

**Option 1: Download pre-built release** (easiest, Windows only)

Download the ZIP from [Releases](https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend), extract it, and run `MissionPlanner.exe`.

**Option 2: Build from fork**

```bash
git clone https://github.com/deepak61296/MissionPlanner.git
cd MissionPlanner
dotnet build MissionPlanner.csproj
```

Once Mission Planner is running:
1. Connect to your vehicle (SITL or real hardware)
2. Press **Ctrl+L** to open the AI chat panel
3. Start typing commands

### MAVProxy

Clone the fork and install:

```bash
git clone -b feature/ai-backend-integration https://github.com/deepak61296/MAVProxy.git
cd MAVProxy
pip install -e .
```

Start MAVProxy and load the module:
```bash
mavproxy.py --master=udp:127.0.0.1:14550 --console
```
```
module load ai_backend
ai_backend enable
```

Now type commands directly in the MAVProxy console:
```
arm the drone
takeoff to 15 meters
move north 30 meters
```

Module commands:
| Command | What it does |
|---------|-------------|
| `ai_backend enable` | Turn on natural language input |
| `ai_backend disable` | Turn it off |
| `ai_backend status` | Check backend connection |
| `ai_backend safe` | Require y/n confirmation for commands |
| `ai_backend unsafe` | Skip confirmations |

### QGroundControl

**Option 1: Download AppImage** (Linux, easiest)

Download from [Releases](https://github.com/deepak61296/qgroundcontrol/releases/tag/ai_backend), make it executable, and run:

```bash
chmod +x QGroundControl-x86_64.AppImage
./QGroundControl-x86_64.AppImage
```

**Option 2: Build from fork**

```bash
git clone https://github.com/deepak61296/qgroundcontrol.git
cd qgroundcontrol
git checkout feature/ai-backend-integration
git submodule update --init --recursive
cmake -B build
cmake --build build -j$(nproc)
./build/Debug/QGroundControl
```

Once QGC is running:
1. Go to **Application Settings** > **AI Backend**
2. Enable the backend and set the URL to `http://localhost:5000`
3. Go to Fly view and press **Ctrl+L** to open the chat panel

## How It Works

```
User (plain English) --> GCS (MAVProxy / MP / QGC)
                              |
                              | HTTP POST /chat
                              v
                         Backend (Flask)
                              |
                              v
                         Ollama (local LLM)
                              |
                              v
                         Command extraction
                              |
                              v
                         GCS executes via MAVLink
```

Two modes:
- **Agent** — executes commands (arm, takeoff, land, move, etc.)
- **Ask** — read-only telemetry queries

## Supported Commands

| Command | Example |
|---------|---------|
| ARM / DISARM | "arm the drone", "disarm" |
| TAKEOFF | "takeoff to 15m" |
| LAND | "land now" |
| RTL | "return home" |
| CHANGE_MODE | "switch to loiter" |
| MOVE_DIRECTION | "move north 20m" |
| ALTITUDE_CHANGE | "go up 10 meters" |
| SET_SPEED | "set speed to 5 m/s" |
| SET_YAW | "face east" |
| GOTO | "fly to 37.77, -122.41" |
| GET_PARAM / SET_PARAM | "what is BATT_CAPACITY?", "set disarm_delay to 40" |
| REBOOT | "reboot" |

## Verification

Make sure the backend is healthy:
```bash
curl http://localhost:5000/health
```

Test with SITL (no real drone needed):
```bash
# Terminal 1: Start ArduPilot SITL
cd ArduCopter && sim_vehicle.py --console --map

# Terminal 2: Start the backend
python run_server.py

# Terminal 3: Start MAVProxy with AI
mavproxy.py --master=udp:127.0.0.1:14550 --console
module load ai_backend
ai_backend enable
```

## Troubleshooting

**Backend won't start** — Make sure Ollama is running (`ollama serve`) and the model is downloaded (`ollama list`).

**Commands not executing** — Check the backend terminal for errors. Run `curl http://localhost:5000/health` to verify the backend is reachable.

**Slow responses** — Use a GPU if available. For CPU-only, try a smaller model: `ollama pull qwen2.5:1.5b` and edit `backend/config.py`.

**Port 5000 in use** — Change `API_PORT` in `backend/config.py` and update the GCS backend URL.

## Project Structure

```
ardupilot-ai-backend/
├── backend/                   # Flask API server
│   ├── api_server.py          # HTTP endpoints
│   ├── planner.py             # LLM task decomposition (the brain)
│   ├── executor.py            # Agentic execution engine (the hands)
│   ├── tools.py               # Tool definitions + JSON extraction
│   ├── commands.py            # Command extraction from LLM output
│   ├── prompts.py             # System prompts for each mode
│   ├── config.py              # Settings and safety limits
│   ├── telemetry_data.py      # Telemetry formatting
│   ├── param_db.py            # ArduPilot parameter RAG database
│   └── mavlink_manager.py     # Direct MAVLink (standalone mode)
├── training/                  # Fine-tuning with Unsloth
│   ├── unsloth_finetuning.ipynb  # Training notebook
│   ├── train_unsloth.py       # Training script
│   └── outputs/               # Training outputs
├── integrations/
│   ├── mavproxy/              # MAVProxy module
│   ├── mission_planner/       # Mission Planner plugin
│   └── qgroundcontrol/        # QGC integration docs
├── demos/                     # Demo videos
├── tests/                     # Test suite
├── docs/                      # Additional documentation
└── requirements.txt
```

## Links

| | |
|---|---|
| QGroundControl fork | https://github.com/deepak61296/qgroundcontrol |
| Mission Planner fork | https://github.com/deepak61296/MissionPlanner |
| MAVProxy fork | https://github.com/deepak61296/MAVProxy/tree/feature/ai-backend-integration |
| MP release (Windows) | https://github.com/deepak61296/MissionPlanner/releases/tag/ai_backend |
| Ollama | https://ollama.com |
| ArduPilot SITL | https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html |
| Issues | https://github.com/deepak61296/ardupilot-ai-backend/issues |

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| RAM | 8 GB | 16 GB |
| GPU | None (CPU works) | NVIDIA GPU |
| Python | 3.10 | 3.10+ |
| Storage | 5 GB | 10 GB |

## Running Tests

```bash
# Run comprehensive test suite
./run_tests.sh

# Or run specific tests
python tests/test_new_tools.py
```

## License

GPL-3.0. Always test in simulation first.
