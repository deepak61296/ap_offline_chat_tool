# Project Overview

## What is ArduPilot AI Backend?

A natural language interface for ArduPilot drones that lets users control vehicles using plain English instead of technical commands. The system runs entirely locally using Ollama and supports both MAVProxy and Mission Planner.

## Core Concept

**Traditional workflow:**
```
User → "mode guided" → MAVProxy → MAVLink → Drone changes mode
```

**AI-enabled workflow:**
```
User → "switch to guided mode" → AI Backend → Command extraction → MAVProxy → MAVLink → Drone changes mode
```

The AI backend translates natural language into structured MAVLink commands while maintaining safety checks and validation.

## Key Features

### Natural Language Control
- **Simple commands**: "arm the drone", "take off to 20 meters", "land now"
- **Complex sequences**: "arm, take off to 15 meters, then move north 50 meters"
- **Telemetry queries**: "what's my battery level?", "how high am I flying?"

### Three Operation Modes

**1. Agent Mode** - Execute commands
```
User: "take off to 30 meters"
AI: "Taking off to 30 meters now."
→ Executes MAV_CMD_NAV_TAKEOFF
```

**2. Ask Mode** - Read-only queries
```
User: "what's my current altitude?"
AI: "You are currently at 15.3 meters above home."
→ No command execution
```

**3. Script Mode** - Lua script generation
```
User: "create a battery monitor script"
AI: Generates complete Lua script with ArduPilot API calls
→ Deploys via MAVFTP (Mission Planner only)
```

### Safety Features
- Altitude limits (max 500m for takeoff)
- Distance limits (max 1000m for movement)
- Risk-based confirmation prompts
- Parameter validation before execution
- Command logging for audit trail

### Offline Operation
- Runs entirely on local machine
- No cloud API calls or internet required
- Uses Ollama for LLM inference
- ArduPilot documentation search via local embeddings

## Technology Stack

**Backend:**
- Python 3.8+
- Flask (HTTP API)
- Ollama (local LLM inference)
- Sentence Transformers (document search)

**LLM Models:**
- qwen2.5-coder:3b (agent/ask modes, fast responses)
- qwen2.5-coder:7b (script mode, better code generation)

**GCS Integration:**
- MAVProxy 1.8+ (Python module)
- Mission Planner 1.3+ (C# plugin)

**Communication:**
- HTTP REST API between GCS and backend
- MAVLink protocol between GCS and vehicle

## Project Structure

```
ardupilot-ai-backend/
├── backend/                 # Core Flask API server
│   ├── api_server.py       # Main HTTP endpoints
│   ├── commands.py         # Command parsing and extraction
│   ├── prompts.py          # LLM system prompts
│   ├── config.py           # Safety limits and settings
│   ├── rag.py              # Document search
│   └── template_injector.py # Lua template system
├── integrations/           # GCS integration code
│   ├── mavproxy/          # MAVProxy module + patch
│   └── mission_planner/   # Mission Planner plugin files
├── models/                 # Ollama model management
├── tests/                  # Test suite
├── docs/                   # Documentation
└── demos/                  # Demo videos
```

## How It Works

### Request Flow

1. **User Input** - User types natural language in GCS
2. **NL Detection** - GCS checks if input is natural language or direct command
3. **HTTP Request** - GCS sends POST /chat with message and telemetry
4. **LLM Processing** - Backend builds prompt and calls Ollama
5. **Response Parsing** - Backend receives natural language response
6. **Command Extraction** - Regex patterns extract structured command
7. **Validation** - Safety checks on parameters and risk level
8. **Return to GCS** - JSON command sent back to GCS
9. **MAVLink Execution** - GCS translates to MAVLink and sends to vehicle
10. **Feedback** - Vehicle state changes, telemetry updates

### Command Extraction Example

**LLM Response:**
```
"Taking off to 25 meters now."
```

**Regex Pattern:**
```python
r'taking off to (\d+)'
```

**Extracted Command:**
```json
{
  "type": "TAKEOFF",
  "params": {
    "altitude": 25
  }
}
```

**MAVLink Translation:**
```python
master.mav.command_long_send(
    target_system,
    target_component,
    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
    0, 0, 0, 0, 0, 0, 0, 25
)
```

## Supported Commands

| Command | Example | Risk Level |
|---------|---------|------------|
| ARM | "arm the drone" | Medium |
| DISARM | "disarm now" | Low |
| TAKEOFF | "take off to 20 meters" | High |
| LAND | "land the drone" | Medium |
| RTL | "return to home" | Medium |
| GOTO | "go to waypoint 2" | Medium |
| MOVE | "move north 50 meters" | Medium |
| ALTITUDE_CHANGE | "climb 10 meters" | Medium |
| SET_MODE | "switch to loiter mode" | Medium |
| SET_SPEED | "set speed to 5 meters per second" | Medium |
| SET_YAW | "turn to heading 180 degrees" | Medium |
| GET_PARAM | "get parameter RTL_ALT" | Low |
| SET_PARAM | "set RTL_ALT to 50" | High |
| LUA_SCRIPT | "create battery monitor script" | High |

## Integration Options

### MAVProxy Integration

**Option 1: Install Module**
```bash
# Copy module to MAVProxy modules directory
cp integrations/mavproxy/mavproxy_ai_backend.py \
   ~/.local/lib/python3.x/site-packages/MAVProxy/modules/

# Load in MAVProxy
module load ai_backend
```

**Option 2: Use Forked MAVProxy**
```bash
git clone https://github.com/deepak61296/MAVProxy.git
cd MAVProxy
git checkout feature/ai-backend-integration
pip install -e .
mavproxy.py --ai-backend
```

### Mission Planner Integration

**Option 1: Use Pre-built Fork**
```bash
# Download from releases
https://github.com/deepak61296/MissionPlanner/releases
```

**Option 2: Build from Source**
```bash
git clone https://github.com/deepak61296/MissionPlanner.git
cd MissionPlanner
# Copy plugin files from integrations/mission_planner/
# Build in Visual Studio
```

## Use Cases

### Flight Testing
```
"arm and take off to 10 meters"
"move forward 20 meters"
"what's my battery voltage?"
"land now"
```

### Parameter Tuning
```
"what's the current RTL altitude?"
"set RTL altitude to 100 meters"
"get all PID parameters"
```

### Script Development
```
"create a geofence script with 500 meter radius"
"generate battery monitor that triggers RTL at 20%"
"make a waypoint follower script"
```

### Training and Education
- New users can learn MAVLink commands through natural language
- Ask mode explains telemetry without risk of execution
- Script mode teaches Lua API through examples

## System Requirements

**Hardware:**
- CPU: 4+ cores (8+ recommended)
- RAM: 8GB minimum (16GB for 7B models)
- Disk: 10GB for models and docs
- GPU: Optional, speeds up inference

**Software:**
- Python 3.8 or higher
- Ollama 0.1.0+
- MAVProxy 1.8+ or Mission Planner 1.3+
- Windows, Linux, or macOS

**Network:**
- Local network connection between GCS and backend (can be same machine)
- No internet required for operation

## Performance

**Typical Response Times:**
- Template-based Lua generation: ~50ms
- LLM command extraction (3B model): 1-2 seconds
- LLM script generation (7B model): 2-4 seconds
- MAVLink execution overhead: ~100ms

**Bottlenecks:**
- LLM inference time (depends on model size and hardware)
- Can use GPU for 2-3x speedup
- Smaller models (3B) faster but slightly less accurate

## Development Status

**Current Version:** 2.3.0

**Completed Features:**
- ✓ MAVProxy integration with input interception
- ✓ Mission Planner plugin with three modes
- ✓ 14 command types with validation
- ✓ Template-based Lua generation
- ✓ LLM fallback for custom scripts
- ✓ RAG system for ArduPilot docs
- ✓ Safety checks and risk levels
- ✓ Comprehensive test suite

**Planned Features:**
- QGroundControl integration
- Voice input support
- Multi-vehicle coordination
- Flight plan generation
- Automated test flight scripts

## Documentation

- **README.md** - Quick start and setup instructions
- **docs/ARCHITECTURE.md** - System architecture and data flow
- **docs/CONTRIBUTING.md** - Developer guide
- **docs/COMPATIBILITY.md** - Version compatibility matrix
- **docs/INSTALL_WINDOWS.md** - Windows installation guide
- **docs/PROJECT_OVERVIEW.md** - This document

## Repository Structure

**Main Repository:**
- https://github.com/deepak61296/ardupilot-ai-backend
- Contains backend server and integration copies

**Integration Forks:**
- https://github.com/deepak61296/MAVProxy (feature/ai-backend-integration branch)
- https://github.com/deepak61296/MissionPlanner (feature/script-mode-clean branch)

## Getting Started

**1. Install Ollama and pull models:**
```bash
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b
```

**2. Create conda environment:**
```bash
conda create -n ardupilot_ai python=3.10
conda activate ardupilot_ai
```

**3. Install backend:**
```bash
cd ardupilot-ai-backend
pip install -r requirements.txt
```

**4. Start backend:**
```bash
python -m backend.api_server
```

**5. Integrate with GCS:**
- For MAVProxy: Load ai_backend module
- For Mission Planner: Press Ctrl+L to open chat

**6. Verify:**
```bash
curl http://localhost:5000/health
```

## License

MIT License - see LICENSE file for details

## Contributing

See docs/CONTRIBUTING.md for development workflow and guidelines.

## Support

For issues and feature requests, please use GitHub Issues on the main repository.
