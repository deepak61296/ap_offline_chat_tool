# ArduPilot AI Backend - Project Overview

## What is it?

A natural language drone control system that runs entirely offline. Talk to your drone in plain English through QGroundControl, Mission Planner, or MAVProxy.

**Version 3.0** - Structured tool calling with Planner/Executor pipeline.

## The Problem

Traditional drone control requires technical MAVLink commands:
```
mode guided
arm throttle
takeoff 20
```

Users need to memorize syntax and remember parameter names.

## The Solution

Natural language interface:
```
"arm the drone and takeoff to 20 meters"
"move north 50m then circle at 10m radius"
"which parameter controls disarm delay?"
```

The AI understands intent and translates to proper commands.

## Key Features

| Feature | Description |
|---------|-------------|
| **Offline** | Runs locally with Ollama, no cloud/API needed |
| **Multi-GCS** | Works with QGroundControl, Mission Planner, MAVProxy |
| **21 Tools** | arm, takeoff, land, move, goto, circle, set_param, etc. |
| **Parameter RAG** | Search 5600+ ArduPilot parameters semantically |
| **Multi-step** | "arm, takeoff, move north 50m" executes as sequence |
| **Safety** | Altitude limits, distance limits, validation |

## Architecture (v3.0)

```
┌─────────────────────────────────────────────────────────────┐
│                  TOOL CALLING PIPELINE                       │
│                                                              │
│   User: "arm and takeoff to 20m"                            │
│              │                                               │
│              ▼                                               │
│   ┌────────────────────────────────────────────────────┐    │
│   │                    PLANNER                          │    │
│   │  • Calls Ollama LLM (qwen2.5:3b)                   │    │
│   │  • LLM outputs JSON tool calls:                    │    │
│   │    [{"tool":"arm"}, {"tool":"takeoff",             │    │
│   │     "params":{"altitude":20}}]                     │    │
│   └──────────────────────┬─────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│   ┌────────────────────────────────────────────────────┐    │
│   │                    EXECUTOR                         │    │
│   │  • Classifies commands                             │    │
│   │  • Handles special flows (CIRCLE, SEARCH_PARAM)    │    │
│   │  • Compiles movements to GPS waypoints             │    │
│   │  • Returns commands to GCS                         │    │
│   └──────────────────────┬─────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│   GCS (QGC/MP/MAVProxy) executes via MAVLink               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Planner (`planner.py`) - The Brain
- Builds system prompt with tool definitions
- Calls Ollama LLM
- Extracts JSON tool calls from response
- Handles RAG re-prompting for parameter lookups

### 2. Executor (`executor.py`) - The Hands
- Classifies commands: immediate, special, backend-only
- Multi-step mission handling
- CIRCLE mode (sets radius param + mode change)
- RAG double-hop for SEARCH_PARAM

### 3. Tools (`tools.py`) - Capabilities
- 21 structured tool definitions
- JSON extraction from LLM output
- Validation and type coercion
- Tool name → command type normalization

### 4. Parameter Database (`param_db.py`) - Knowledge
- 5600+ ArduPilot parameters indexed
- TF-IDF semantic search
- Prefix boosting (BATT_ for battery queries)
- SIM_ parameter deprioritization

## Supported Commands

| Category | Commands |
|----------|----------|
| **Basic** | arm, disarm, takeoff, land, rtl |
| **Movement** | move (N/S/E/W/forward/backward), goto |
| **Mode** | change_mode, pause, resume |
| **Parameters** | get_param, set_param, search_param, explain_param |
| **Info** | get_status, get_position |
| **Advanced** | circle, set_speed, set_altitude, set_heading |

## How RAG Works

When user asks "which parameter sets disarm delay?":

```
1. LLM outputs: [{"tool":"search_param", "params":{"query":"disarm delay"}}]

2. Executor detects SEARCH_PARAM → triggers RAG

3. Search param_db:
   - DISARM_DELAY: "Time before auto-disarm after landing"
   - MOT_SAFE_TIME: "Motor output safety delay"
   - etc.

4. Inject results into context, re-prompt LLM

5. LLM explains parameters in natural language

6. Return informational response (no command to GCS)
```

## API Contract

```
POST /chat
{
  "message": "takeoff to 25 meters",
  "mode": "agent",
  "telemetry": {...}
}

Response:
{
  "response": "Taking off to 25 meters.",
  "command": {"type": "TAKEOFF", "params": {"altitude": 25}},
  "success": true
}
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Ollama + qwen2.5:3b (local, offline) |
| **Backend** | Python, Flask |
| **Search** | TF-IDF vectorization, cosine similarity |
| **GCS** | QGroundControl, Mission Planner, MAVProxy |
| **Protocol** | MAVLink |

## Performance

| Operation | Time |
|-----------|------|
| LLM inference (3B) | 1-2s |
| Parameter search | ~10ms |
| RAG re-prompt | +1-2s |
| End-to-end | 1-3s |

## Test Coverage

```
./run_tests.sh

✓ Unit tests: 39/39 passed
✓ Syntax check: passed
✓ Parameter DB: 6/6 tests passed
✓ Tool definitions: 9/9 tests passed
✓ Integration tests: 23/23 passed
```

## Quick Start

```bash
# 1. Install Ollama and model
ollama pull qwen2.5:3b

# 2. Clone and install
git clone https://github.com/deepak61296/ardupilot-ai-backend.git
cd ardupilot-ai-backend
pip install -r requirements.txt

# 3. Start backend
python run_server.py

# 4. Test
curl http://localhost:5000/health
```

## GCS Integration

**QGroundControl**: Download fork, enable AI backend in settings, Ctrl+L for chat

**Mission Planner**: Download release, Ctrl+L for chat panel

**MAVProxy**: `module load ai_backend && ai_backend enable`

## Key Design Decisions

1. **Structured tool calling over regex** - JSON tools more robust than parsing
2. **Local LLM** - Privacy-first, no cloud dependency
3. **Backend-only commands** - Info queries don't pollute GCS
4. **RAG double-hop** - Search → inject → re-prompt for accuracy
5. **Separation of concerns** - Planner + Executor

## Future Work

- **Full agentic loop**: Observation-action cycles with retry logic
- **Telemetry feedback**: Observe results, adjust next action
- **Memory**: Persistent context across requests
- **Autonomous missions**: Multi-step reasoning without user input

## Repository

- Backend: https://github.com/deepak61296/ardupilot-ai-backend
- QGC Fork: https://github.com/deepak61296/qgroundcontrol
- Mission Planner Fork: https://github.com/deepak61296/MissionPlanner
- MAVProxy Fork: https://github.com/deepak61296/MAVProxy

## License

GPL-3.0
