# Architecture

ArduPilot AI Backend enables natural language drone control through local LLMs.

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                            User Layer                             │
└──────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
          ┌─────────▼─────────┐       ┌────────▼────────┐
          │   MAVProxy CLI    │       │ Mission Planner │
          │   + AI Module     │       │   + AI Plugin   │
          └─────────┬─────────┘       └────────┬────────┘
                    │                           │
                    │   HTTP POST /chat         │
                    │   (Natural Language)      │
                    │                           │
                    └─────────────┬─────────────┘
                                  │
┌──────────────────────────────────────────────────────────────────┐
│                         Backend Layer                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Flask API Server (backend/api_server.py)                  │ │
│  │  - /chat endpoint (Agent/Ask modes)                        │ │
│  │  - /health endpoint                                        │ │
│  └──────────────────┬──────────────────────┬──────────────────┘ │
│                     │                      │                     │
│          ┌──────────▼──────────┐  ┌────────▼──────────┐         │
│          │  Command Parser     │  │  Prompt Engine    │         │
│          │  (commands.py)      │  │  (prompts.py)     │         │
│          │  - Regex extraction │  │  - Mode-specific  │         │
│          │  - Validation       │  │    prompts        │         │
│          │  - Safety checks    │  │  - Context mgmt   │         │
│          └──────────┬──────────┘  └────────┬──────────┘         │
│                     │                      │                     │
│                     └──────────┬───────────┘                     │
│                                │                                 │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Ollama Service        │
                    │   - qwen2.5:3b    │
                    │   - Local inference     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   LLM Response          │
                    │   (Natural Language)    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Command Extraction     │
                    │  {"type": "ARM", ...}   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Return to GCS          │
                    └────────────┬────────────┘
                                 │
┌──────────────────────────────────────────────────────────────────┐
│                        Execution Layer                            │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  MAVLink Command Execution                                  ││
│  │  - MAV_CMD_COMPONENT_ARM_DISARM                            ││
│  │  - MAV_CMD_NAV_TAKEOFF / MAV_CMD_NAV_LAND                  ││
│  │  - MAV_CMD_DO_SET_MODE                                     ││
│  │  - MAV_CMD_DO_REPOSITION                                   ││
│  │  - MAV_CMD_DO_CHANGE_SPEED                                 ││
│  │  - MAV_CMD_CONDITION_YAW                                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                  │                                │
│                                  ▼                                │
│                    ┌──────────────────────────┐                  │
│                    │  ArduPilot Vehicle       │                  │
│                    │  (SITL / Real Hardware)  │                  │
│                    └──────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Backend Server (`backend/`)

Flask HTTP API that processes natural language and returns structured commands.

**Key files:**
- `api_server.py` - Main HTTP server with /chat and /health endpoints
- `commands.py` - Command extraction using regex patterns and validation logic
- `prompts.py` - Mode-specific system prompts for LLM
- `config.py` - Safety limits, risk levels, model settings
- `planner.py` - LLM planner for structured tool calls
- `executor.py` - Command sequencing and execution orchestration

**API Contract:**
```json
Request: POST /chat
{
  "message": "arm the drone and take off to 10 meters",
  "mode": "agent",
  "telemetry": {
    "armed": false,
    "mode": "STABILIZE",
    "battery": 12.4,
    "lat": 37.7749,
    "lon": -122.4194,
    "alt": 0
  }
}

Response:
{
  "reply": "Arming drone and taking off to 10 meters.",
  "command": {
    "type": "ARM",
    "params": {}
  }
}
```

### 2. GCS Integrations (`integrations/`)

**MAVProxy Module** (`integrations/mavproxy/`)
- Hooks into MAVProxy's input handler
- Detects natural language vs MAVProxy commands
- Sends NL requests to backend via HTTP
- Executes returned commands through MAVLink
- Two integration options:
  1. Install module file directly
  2. Use forked MAVProxy with --ai-backend flag

**Mission Planner Plugin** (`integrations/mission_planner/`)
- C# chat interface accessible via Ctrl+L
- Agent and Ask modes
- Backend URL configuration in settings
- Two integration options:
  1. Use pre-built fork exe
  2. Build from source with plugin files

### 3. Operation Modes

**Agent Mode** (Execute commands)
- Full drone control with safety validation
- Supported commands: ARM, DISARM, TAKEOFF, LAND, RTL, GOTO, MOVE, ALTITUDE_CHANGE, SET_MODE, SET_SPEED, SET_YAW, GET_PARAM, SET_PARAM
- Requires y/n confirmation for high-risk commands in safe mode
- All actions logged with timestamp

**Ask Mode** (Read-only)
- Telemetry queries only, no command execution
- Access to: battery, GPS, altitude, speed, heading, mode
- Used for flight status monitoring
- Cannot modify vehicle state

### 4. Safety System

**Command Validation** (`backend/config.py`)
```python
COMMAND_RISK_LEVELS = {
    "ARM": "medium",
    "TAKEOFF": "high",
    "GOTO": "medium",
    "SET_PARAM": "high"
}

MAX_TAKEOFF_ALTITUDE = 500  # meters
MAX_GOTO_DISTANCE = 1000    # meters
```

**Execution Flow:**
1. Parse command from LLM response
2. Validate parameters (range checks, type checks)
3. Check risk level
4. Prompt user confirmation if high/critical risk
5. Execute via MAVLink
6. Log action and result

### 5. Document Retrieval (RAG)

**ArduPilot Documentation Search** (`backend/rag.py`)
- Offline search through local ArduPilot docs
- Uses sentence transformers for semantic similarity
- Returns top-k relevant chunks with sources
- Integrated into Ask mode for technical queries
- No external API calls required

## Data Flow

```
┌─────────────────┐
│  User Input     │  "take off to 20 meters"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ NL Detection    │  Check if natural language or direct command
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTTP Request    │  POST /chat with message + telemetry
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Prompt Build    │  System prompt + context + user message
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Call        │  Ollama inference (1-3s)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Response Parse  │  "Taking off to 20 meters now."
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Regex Extract   │  Find "TAKEOFF" trigger + altitude param
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Command Valid.  │  Check altitude <= 500m, create JSON
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return to GCS   │  {"type": "TAKEOFF", "params": {"altitude": 20}}
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MAVLink Exec    │  MAV_CMD_NAV_TAKEOFF with altitude 20
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vehicle Action  │  Motors spin up, climb to 20m
└─────────────────┘
```

## Extension Guide

To add a new command type:

1. **Define trigger in prompts** (`backend/prompts.py`)
```python
AGENT_MODE_PROMPT += """
- Circle: "Circling at radius X meters."
"""
```

2. **Add extraction logic** (`backend/commands.py`)
```python
def extract_circle_command(text):
    match = re.search(r'radius (\d+)', text)
    if match:
        return {"type": "CIRCLE", "params": {"radius": int(match.group(1))}}
```

3. **Add validation** (`backend/config.py`)
```python
COMMAND_RISK_LEVELS["CIRCLE"] = "medium"
```

4. **Update GCS integration** (`integrations/mavproxy/mavproxy_ai_backend.py`)
```python
elif cmd_type == "CIRCLE":
    radius = params.get('radius', 0)
    self.master.mav.command_long_send(...)
```

## Performance Metrics

| Operation | Time |
|-----------|------|
| Template match | ~50ms |
| LLM inference (3B) | 1-2s |
| LLM inference (7B) | 2-4s |
| MAVLink exec | ~100ms |
| End-to-end | 1.5-4s |

Bottleneck: LLM inference time depends on model size and hardware (CPU vs GPU).

## System Requirements

**Minimum:**
- Python 3.8+
- 8GB RAM
- 4GB disk space
- CPU: 4 cores

**Recommended:**
- Python 3.10+
- 16GB RAM
- 10GB disk space
- CPU: 8 cores or GPU

**Software:**
- Ollama 0.1.0+
- MAVProxy 1.8+ or Mission Planner 1.3+
- Windows/Linux/macOS
