# Architecture

ArduPilot AI Backend v3.0 - Natural language drone control through local LLMs with structured tool calling.

> **Note**: Current implementation uses structured JSON tool calling. Full agentic architecture (autonomous looping, observation-action cycles, memory) is planned for future versions.

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   QGroundControl │  │  Mission Planner │  │   MAVProxy CLI   │          │
│  │   (AI Chat Box)  │  │   (Ctrl+L Chat)  │  │   (ai: prefix)   │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │ HTTP POST /chat
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND SERVER (Flask)                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API Layer (api_server.py)                    │   │
│  │   POST /chat    POST /health    POST /status                        │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │                      PLANNER (planner.py)                            │   │
│  │  • Builds system prompt with tool definitions                        │   │
│  │  • Calls Ollama LLM (qwen2.5:3b)                                    │   │
│  │  • Extracts JSON tool calls from response                           │   │
│  │  • Supports RAG re-prompting for parameter lookups                  │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │                      EXECUTOR (executor.py)                          │   │
│  │  • Classifies commands (immediate vs special vs backend-only)       │   │
│  │  • Handles multi-step missions (ARM → TAKEOFF → MOVE sequences)     │   │
│  │  • Compiles movement sequences into GPS waypoints                   │   │
│  │  • Manages CIRCLE mode (sets radius, changes mode)                  │   │
│  │  • RAG double-hop for SEARCH_PARAM                                  │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────┐  ┌────────────┴───────────┐  ┌───────────────────────┐   │
│  │  tools.py    │  │   param_db.py          │  │  mavlink_manager.py   │   │
│  │  21 tools    │  │   5600+ params         │  │  Direct MAVLink ops   │   │
│  │  JSON schema │  │   Semantic search      │  │  (optional)           │   │
│  └──────────────┘  └────────────────────────┘  └───────────────────────┘   │
│                                                                              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ JSON Command
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GROUND CONTROL STATION                              │
│  Receives: {"type": "TAKEOFF", "params": {"altitude": 20}}                  │
│  Executes: MAVLink MAV_CMD_NAV_TAKEOFF                                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARDUPILOT VEHICLE                                    │
│                    (SITL Simulator or Real Hardware)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tool Calling Pipeline (v3.0)

The backend uses **structured JSON tool calling** instead of fragile regex parsing:

```
┌─────────────────────────────────────────────────────────────────┐
│                  TOOL CALLING PIPELINE                           │
│                                                                  │
│   User: "arm and takeoff to 20m then move north 50m"           │
│                          │                                       │
│                          ▼                                       │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                    PLANNER                                │  │
│   │  1. Build prompt with TOOL_DEFINITIONS                   │  │
│   │  2. Call LLM → get response with JSON tool calls         │  │
│   │  3. Extract: [{"tool":"arm"}, {"tool":"takeoff",         │  │
│   │               "params":{"altitude":20}},                  │  │
│   │               {"tool":"move", "params":{"direction":     │  │
│   │               "north", "distance":50}}]                   │  │
│   └──────────────────────────┬───────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                    EXECUTOR                               │  │
│   │  1. Classify each command                                 │  │
│   │  2. ARM, TAKEOFF → immediate (queue for GCS)             │  │
│   │  3. MOVE → movement (compile to GPS waypoint)            │  │
│   │  4. Build execution plan                                  │  │
│   │  5. Return commands to GCS for execution                 │  │
│   └──────────────────────────┬───────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│   Output: {"command": {"type":"ARM"}, "commands": [...]}        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Tool Definitions (`backend/tools.py`)

21 structured tools the LLM can call:

| Tool | Description | Parameters |
|------|-------------|------------|
| `arm` | Arm drone motors | none |
| `disarm` | Disarm drone motors | none |
| `takeoff` | Take off to altitude | `altitude` (meters) |
| `land` | Land at current position | none |
| `rtl` | Return to launch | none |
| `move` | Move in direction | `direction`, `distance` |
| `circle` | Orbit at radius | `radius` (meters) |
| `goto` | Fly to GPS coords | `latitude`, `longitude`, `altitude` |
| `change_mode` | Change flight mode | `mode` |
| `set_speed` | Set ground speed | `speed` (m/s) |
| `set_altitude` | Change altitude | `change` (meters) |
| `set_heading` | Set yaw/heading | `heading` (degrees) |
| `get_param` | Read parameter | `name` |
| `set_param` | Write parameter | `name`, `value` |
| `search_param` | Search param database | `query` |
| `get_status` | Get drone status | none |
| `get_position` | Get GPS position | none |
| `pause` | Hover in place (LOITER) | none |
| `resume` | Resume mission (AUTO) | none |
| `explain_param` | Explain parameter | `name` |
| `reboot` | Reboot flight controller | none |

### 2. Planner (`backend/planner.py`)

The "brain" that interprets user intent:

```python
def plan(user_message, telemetry, model) -> (ai_text, commands):
    # 1. Build system prompt with tool definitions
    prompt = get_agent_prompt(connection_status, telemetry)

    # 2. Call Ollama LLM
    response = ollama.chat(model=model, messages=[...])

    # 3. Extract JSON tool calls from response
    text, tool_calls = extract_tool_calls(response)

    # 4. Normalize to command format
    commands = [normalize_tool_call(tc) for tc in tool_calls]

    return text, commands
```

### 3. Executor (`backend/executor.py`)

The "hands" that process and sequence commands:

**Command Classification:**
- `IMMEDIATE`: ARM, DISARM, TAKEOFF, LAND, RTL, CHANGE_MODE, GOTO, SET_SPEED, etc.
- `SPECIAL`: CIRCLE, SEARCH_PARAM, MISSION_PLAN, GET_STATUS, GET_POSITION
- `BACKEND_ONLY`: SEARCH_PARAM, GET_STATUS, GET_POSITION, EXPLAIN_PARAM (never sent to GCS)

**Special Flows:**
- **Multi-step missions**: ARM + TAKEOFF + MOVEs → uploads waypoint mission
- **CIRCLE mode**: Sets CIRCLE_RADIUS param, then changes mode
- **SEARCH_PARAM**: RAG lookup → re-prompts LLM with results
- **Movement compilation**: Converts direction+distance to GPS coordinates

### 4. Parameter Database (`backend/param_db.py`)

Semantic search over 5600+ ArduPilot parameters:

```python
# Search for parameters
results = db.search("battery failsafe", top_k=5)
# Returns: [{"name": "BATT_FS_LOW_VOLT", "description": "...", "range": "..."}]
```

Features:
- TF-IDF vectorization with cosine similarity
- Prefix boosting (BATT_ for battery queries, MOT_ for motor queries)
- SIM_ parameter deprioritization
- Numbered suffix handling (BATT_ ranked higher than BATT2_)

### 5. JSON Tool Calling (`backend/tools.py`)

LLM outputs structured JSON instead of free-text:

```
User: "take off to 25 meters"

LLM Response:
Taking off to 25 meters now.
```json
[{"tool": "takeoff", "params": {"altitude": 25}}]
```
```

**Extraction strategies:**
1. Look for ```json code blocks
2. Look for raw JSON arrays [...]
3. Look for single JSON objects {"tool": ...}

**Validation & coercion:**
- Validates tool name against VALID_TOOLS set
- Coerces string numbers to int/float ("25" → 25)
- Preserves confidence scores if present

## API Contract

### POST /chat

```json
Request:
{
  "message": "arm and take off to 20 meters",
  "mode": "agent",
  "model": "qwen2.5:3b",
  "telemetry": {
    "status": {"armed": false, "mode": "STABILIZE"},
    "battery": {"voltage": 12.4, "remaining": 85},
    "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 0}
  }
}

Response:
{
  "success": true,
  "response": "Arming and taking off to 20 meters.",
  "command": {"type": "ARM", "params": {}},
  "commands": [
    {"type": "ARM", "params": {}},
    {"type": "TAKEOFF", "params": {"altitude": 20}}
  ],
  "mode": "agent",
  "model": "qwen2.5:3b"
}
```

### POST /health

```json
Response:
{
  "status": "healthy",
  "service": "ArduPilot AI Backend",
  "version": "3.0.0",
  "operation_mode": "integrated",
  "mavlink_status": "connected" | "not_available"
}
```

## Data Flow Example

```
User: "which parameter controls disarm delay?"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ PLANNER: LLM outputs search_param tool                      │
│ [{"tool": "search_param", "params": {"query": "disarm"}}]  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ EXECUTOR: Detects SEARCH_PARAM → triggers RAG              │
│ 1. Search param_db for "disarm delay"                      │
│ 2. Find: DISARM_DELAY, MOT_SAFE_TIME, etc.                 │
│ 3. Inject results into context                              │
│ 4. Re-prompt LLM with parameter info                       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ RESPONSE: Informational text (no command to GCS)           │
│ "DISARM_DELAY controls how long the drone waits before     │
│  automatically disarming after landing..."                  │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
ardupilot-ai-backend/
├── backend/
│   ├── api_server.py      # Flask HTTP server
│   ├── planner.py         # LLM planning layer
│   ├── executor.py        # Command execution layer
│   ├── tools.py           # Tool definitions & JSON extraction
│   ├── param_db.py        # Parameter database with search
│   ├── prompts.py         # System prompts for agent/ask modes
│   ├── commands.py        # Command validation
│   ├── config.py          # Safety limits, risk levels
│   └── mavlink_manager.py # Direct MAVLink operations (optional)
├── integrations/
│   ├── qgroundcontrol/    # QGC with AI chat (forked)
│   ├── mission_planner/   # Mission Planner plugin
│   └── mavproxy/          # MAVProxy module
├── tests/
│   ├── test_new_tools.py  # Unit tests for tools
│   └── test_agentic_pipeline.py  # Integration tests
├── docs/
│   └── ARCHITECTURE.md    # This file
├── run_server.py          # Server entry point
└── run_tests.sh           # Test runner
```

## Performance

| Operation | Time |
|-----------|------|
| JSON extraction | ~5ms |
| LLM inference (qwen2.5:3b) | 1-2s |
| Parameter search | ~10ms |
| RAG re-prompt | +1-2s |
| End-to-end simple command | 1-3s |
| End-to-end with RAG | 2-4s |

## System Requirements

**Minimum:**
- Python 3.8+
- 8GB RAM
- Ollama with qwen2.5:3b model
- 4GB disk space

**Recommended:**
- Python 3.10+
- 16GB RAM
- GPU for faster inference
- 10GB disk space

## Key Design Decisions

1. **Structured tool calling over regex**: JSON tool calls more robust than regex parsing
2. **Local LLM**: Privacy-first, no cloud API needed
3. **Backend-only commands**: Info queries don't pollute GCS command stream
4. **RAG double-hop**: Search → inject → re-prompt for accurate parameter info
5. **JSON validation**: Type coercion and tool name validation prevents errors
6. **Separation of concerns**: Planner (interprets intent) + Executor (processes commands)

## Future Work: Full Agentic Architecture

Current implementation is **single-pass tool calling**. Future versions will add true agentic capabilities:

| Feature | Current | Future (Agentic) |
|---------|---------|------------------|
| Execution | Single LLM call → commands | Observation-action loop |
| Error handling | Return error to user | Retry with different approach |
| Memory | Stateless per request | Persistent context |
| Planning | LLM outputs all tools at once | Step-by-step reasoning |
| Feedback | None | Observe telemetry, adjust |

**Planned agentic features:**
- Autonomous retry on command failure
- Telemetry observation between actions
- Multi-turn reasoning for complex missions
- Learning from past interactions
