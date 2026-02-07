# Architecture

ArduPilot AI Backend enables natural language drone control through local LLMs.

## System Overview

```
┌─────────────────┐
│   GCS (User)    │
│  MAVProxy / MP  │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  Backend Server │
│  (Flask+Ollama) │
└────────┬────────┘
         │ Local
         ▼
┌─────────────────┐
│  Ollama + LLM   │
│  (qwen/llama)   │
└─────────────────┘
```

## Components

### 1. Backend Server (`backend/`)

Flask HTTP API that:
- Receives natural language from GCS
- Calls local Ollama LLM
- Extracts commands from AI response
- Returns structured commands to GCS

**Key files:**
- `api_server.py` - Main HTTP server
- `commands.py` - Command extraction/validation
- `prompts.py` - AI system prompts
- `config.py` - Safety limits and settings

### 2. GCS Integrations (`integrations/`)

**MAVProxy Module:**
- Intercepts user input before MAVProxy
- Sends natural language to backend
- Executes returned commands via MAVLink

**Mission Planner Plugin:**
- Chat UI in Mission Planner
- Three modes: Agent (execute), Ask (read-only), Script (Lua generation)
- Direct MAVFTP for flashing Lua scripts

### 3. MAVLink Communication

Commands flow:
1. User types: "arm the drone"
2. GCS → Backend: `POST /chat {"message": "arm the drone", "telemetry": {...}}`
3. Backend → LLM: System prompt + user message
4. LLM → Backend: "Arming the drone now."
5. Backend extracts: `{"type": "ARM", "params": {}}`
6. Backend → GCS: Command JSON
7. GCS → Vehicle: MAVLink `MAV_CMD_COMPONENT_ARM_DISARM`

## Operation Modes

### Agent Mode
Full control - executes commands:
- ARM/DISARM
- TAKEOFF/LAND/RTL
- Movement (GOTO, MOVE_DIRECTION)
- Altitude/speed/yaw changes
- Parameter get/set

### Ask Mode
Read-only telemetry queries:
- Battery status
- GPS information
- Flight mode
- Position/altitude

### Script Mode
Lua script generation:
- Template-based (instant, 96% coverage)
- LLM fallback for custom requests
- Syntax validation
- Post-processing for common mistakes

## Safety

**Command Validation:**
- Altitude limits (max 500m for takeoff)
- Distance limits (max 1000m for movement)
- Mode whitelist
- Risk levels (low/medium/high/critical)

**Execution:**
- Safe mode: Requires y/n confirmation
- Unsafe mode: Direct execution
- All commands logged

## Models

**Default:** `qwen2.5-coder:3b` (agent/ask modes)
**Script:** `qwen2.5-coder:7b` (lua generation)

Uses Ollama for local inference - no cloud APIs.

## Data Flow

```
User Input
    ↓
NL Detection (is this natural language or MAVProxy command?)
    ↓
Backend API Call
    ↓
AI Processing (Ollama)
    ↓
Command Extraction (regex patterns)
    ↓
Validation (safety checks)
    ↓
MAVLink Execution
    ↓
Telemetry Feedback
```

## Extension

To add new commands:
1. Add trigger phrase to `prompts.py`
2. Add extraction logic to `commands.py`
3. Add validation in `validate_command()`
4. Add execution in GCS integration

## Performance

- Template matching: ~50ms
- LLM inference: 1-3s (depends on model/hardware)
- MAVLink execution: ~100ms
- End-to-end: 1.5-4s typical

## Requirements

- Python 3.8+
- Ollama with compatible model
- MAVProxy 1.8+ or Mission Planner
- 8GB RAM minimum (16GB recommended for 7B models)
