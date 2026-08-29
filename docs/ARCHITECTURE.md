# Architecture

This document is the main technical walkthrough of the project. It describes the runtime flow, the main folders, and the purpose of the core backend files.

## Project summary

The repo is a local Python backend for natural-language ArduPilot control. A client such as Mission Planner, MAVProxy, or QGroundControl sends a chat request plus telemetry. The backend calls a local Ollama model, converts the model output into structured commands, and returns commands for the client to execute. In standalone mode it can also talk to the vehicle directly through `pymavlink`.

## Top-level structure

```text
ardupilot-ai-backend/
├── backend/                # Main Python application
├── docs/                   # Project documentation
├── integrations/           # GCS-side integration copies
├── tests/                  # Unit and HTTP-level tests
├── training/               # Fine-tuning and dataset experiments
├── run_server.py           # Server entrypoint
├── requirements.txt        # Python dependencies
└── run_tests.sh            # Test helper
```

## Runtime architecture

```text
Client UI / GCS
  -> POST /chat with message + mode + telemetry
  -> backend/api_server.py
  -> ask path or command path
  -> ollama chat
  -> structured command objects
  -> JSON response to client
  -> client executes MAVLink commands
```

**Pipeline flow (agent mode):**

```text
api_server.py      planner.py        tools.py         executor.py
     |                 |                 |                 |
     |--user msg------>|                 |                 |
     |                 |--ollama.chat--->|                 |
     |                 |<--raw response--|                 |
     |                 |--extract_tool_calls-------------->|
     |                 |<--normalized cmds-----------------|
     |                 |                 |--execute------->|
     |<--JSON response-|                 |<--result--------|
```

Two runtime modes are defined in `backend/config.py`:

- `integrated`: default. External client sends telemetry and executes returned commands.
- `standalone`: backend connects directly to the vehicle over MAVLink.

## Request flow

### Ask mode

Used for information only.

1. `backend/api_server.py` receives `POST /chat`.
2. Request is validated and telemetry is checked.
3. `backend/telemetry_data.py` formats telemetry into prompt text.
4. `backend/prompts.py:get_ask_prompt()` builds the ask-mode prompt.
5. `ollama.chat()` returns text.
6. API response contains text and no command.

### Command path

Used when `mode=agent`.

1. `backend/api_server.py` receives `POST /chat`.
2. Telemetry context and connection status are built.
3. `backend/planner.py` sends the request to Ollama with tool descriptions.
4. `backend/tools.py` extracts JSON tool calls from the model output.
5. `backend/tools.py` normalizes tool calls into backend command structs.
6. `backend/executor.py` validates, classifies, and transforms the command sequence.
7. The API returns:
   - `response`: user-facing text
   - `command`: first command for backward compatibility
   - `commands`: ordered list when multiple commands are queued

```json
{
  "response": "Arming and taking off to 20 meters.",
  "command": {"type": "ARM", "params": {}},
  "commands": [
    {"type": "ARM", "params": {}},
    {"type": "TAKEOFF", "params": {"altitude": 20}}
  ]
}
```

## Main backend files

### `backend/api_server.py`

This is the HTTP layer and main orchestrator.

Responsibilities:

- creates the Flask app
- exposes all REST endpoints
- routes `/chat` by mode
- builds telemetry context for prompts
- initializes standalone MAVLink connection when enabled

Main endpoints:

- `GET /health`
- `GET /status`
- `GET /models`
- `POST /chat`
- `GET /test`
- `POST /connect`
- `POST /disconnect`
- `GET /telemetry`
- `POST /command`

### `backend/config.py`

Central configuration and safety constants.

Responsibilities:

- parses startup flags like `--standalone`, `--connect`, `--baud`, `--no-gpu`, `--low-power`
- defines API host and port
- defines default model and Ollama options
- stores command limits such as max takeoff altitude and max movement distance
- defines supported flight modes
- defines operation mode and approval mode

This file is where interviewer-style questions about runtime configuration, limits, or deployment defaults should usually be answered from.

### `backend/prompts.py`

Contains the system prompts for both ask mode and command mode.

Responsibilities:

- defines the command-mode prompt with examples
- injects tool descriptions into the prompt
- defines the ask-mode prompt that explicitly disables command execution
- provides `get_agent_prompt()` and `get_ask_prompt()`

This file is important because command behavior depends heavily on prompt rules. The current design uses prompt instructions plus tool definitions, not pure regex matching.

### `backend/tools.py`

Defines the model-facing tool schema and JSON extraction logic.

Responsibilities:

- declares `TOOL_DEFINITIONS`
- formats tool descriptions for the prompt
- extracts JSON blocks, arrays, or objects from the LLM output
- validates tool names
- coerces parameter types
- converts tool calls into normalized backend commands

```python
# Extract JSON from LLM output
json_block = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
parsed = json.loads(json_block.group(1))

# Normalize to backend command format
TOOL_MAP = {
    "arm":     lambda p: {"type": "ARM", "params": {}},
    "takeoff": lambda p: {"type": "TAKEOFF", "params": {"altitude": p.get("altitude", 10)}},
}
```

Examples of tool names defined here:

- `arm`
- `takeoff`
- `move`
- `goto`
- `set_param`
- `search_param`
- `get_status`
- `pause`
- `resume`

This is the key boundary between model output and deterministic backend logic.

### `backend/planner.py`

This is the model-calling layer for command requests.

Responsibilities:

- builds the message list for Ollama
- calls `ollama.chat()`
- extracts tool calls from raw model output
- normalizes those tool calls into command objects
- re-prompts the model with injected context for parameter lookup flows

```python
response = ollama.chat(
    model=model,
    messages=messages,
    options={'num_ctx': OLLAMA_NUM_CTX, 'temperature': 0.1}
)
raw_response = response['message']['content'].strip()
```

The planner does not execute commands. It only interprets user intent and returns structured actions.

### `backend/executor.py`

This is the command processing layer.

Responsibilities:

- validates normalized commands
- injects prerequisites like `ARM` before `TAKEOFF` when needed
- separates immediate commands from special flows
- handles information-only commands internally
- compiles multiple movement steps into waypoint missions
- handles `CIRCLE`, `SEARCH_PARAM`, `GET_STATUS`, `GET_POSITION`, and parameter explanation flows

```python
for cmd in commands:
    is_valid, error = validate_command(cmd)
    if not is_valid:
        continue
    if cmd['type'] == 'SEARCH_PARAM':
        plan_steps.append(('search', cmd))
    elif cmd['type'] in IMMEDIATE_COMMANDS:
        plan_steps.append(('immediate', cmd))
```

Important behavior:

- backend-only informational commands are filtered out before returning commands to the client
- if PyMAVLink is connected, some prerequisite steps may execute directly on the backend
- movement sequences can become uploaded missions instead of a series of raw move commands

### `backend/commands.py`

This file is partly legacy and partly still active.

Responsibilities:

- validates command structs in `validate_command()`
- contains regex-based extraction helpers from older versions
- defines parameter checks for commands like `TAKEOFF`, `GOTO`, `SET_SPEED`, and `CIRCLE`

Current status:

- validation is still important
- regex extraction helpers are no longer the primary path for `/chat`

### `backend/param_db.py`

Local parameter lookup module.

Responsibilities:

- loads `backend/apm.pdef.json`
- downloads the ArduCopter parameter file if cache is missing
- flattens grouped parameter data
- ranks matches for search queries

Current implementation details:

- keyword-based ranking
- prefix boosts for domains like battery, GPS, failsafe
- penalties for simulation/display style params
- not a vector database

### `backend/telemetry_data.py`

Defines telemetry data structures and prompt formatting helpers.

Responsibilities:

- provides dataclasses for battery, GPS, attitude, speed, status, mission, home, and sensors
- converts telemetry objects to dictionaries
- formats client telemetry into plain text for LLM context

This file matters because the model only sees what this formatter includes.

### `backend/mavlink_manager.py`

Optional direct MAVLink layer for standalone execution.

Responsibilities:

- opens TCP, UDP, or serial MAVLink connections
- waits for heartbeat
- requests telemetry streams
- maintains live telemetry state
- exposes command execution helpers and mission upload support

This file is only active when `pymavlink` is installed and standalone features are used.

### `backend/__init__.py`

Package export file.

Responsibilities:

- exposes the app, planner, executor, tool helpers, config, and optional MAVLink manager
- defines package version metadata

It is small, but useful for understanding the public surface of the backend package.

## Special flows worth explaining in interviews

### Parameter search flow

User asks something like "which parameter controls disarm delay?"

1. Planner emits `search_param`
2. Executor queries `param_db`
3. Matching parameters are injected back into model context
4. Planner is called again with the extra context
5. Backend returns explanation text, and may return a parameter command if appropriate

This is the closest thing in the current code to a multi-step reasoning flow, but it is still a bounded pipeline, not a general autonomous agent loop.

### Multi-move mission flow

User asks for several movement steps.

1. Planner emits multiple `move` tool calls
2. Executor converts them to `MOVE_DIRECTION` commands
3. If enough telemetry is available, executor computes waypoint coordinates
4. If MAVLink is available, the mission is uploaded and backend returns `CHANGE_MODE AUTO`

### Pause and resume

These are model-facing tools, but executor maps them to mode changes:

- `PAUSE` -> `CHANGE_MODE LOITER`
- `RESUME` -> `CHANGE_MODE AUTO`

## Integrations folder

`integrations/` contains copies of client-side integration code, not the main backend runtime.

Important files:

- `integrations/mission_planner/AIBackendService.cs`: calls backend endpoints
- `integrations/mission_planner/DroneCommandExecutor.cs`: executes command objects in Mission Planner
- `integrations/mavproxy/mavproxy_ai_backend.py`: MAVProxy module that forwards natural language to the backend
- `integrations/qgroundcontrol/README.md`: notes for QGroundControl integration

These files are useful when explaining how the backend is consumed by external tools.

## Tests

`tests/` covers both pure Python logic and HTTP behavior.

Important files:

- `test_new_tools.py`: tool definition and normalization coverage
- `test_comprehensive.py`: broad backend checks
- `test_agentic_pipeline.py`: HTTP-level end-to-end checks against a running backend
- `test_command_dataset.py`: command dataset checks
- `test_param_dataset.py`: parameter lookup checks

## Design notes

Current architecture is best described as:

- local LLM-assisted command parsing
- deterministic Python execution pipeline
- structured command response contract

It is not best described as a fully autonomous agent. The current code is mostly a request pipeline with a few controlled multi-step flows.

## Interview explanation

A concise way to explain the project:

1. A GCS sends chat text and telemetry to a Flask backend.
2. The backend uses a local Ollama model to convert natural language into structured tool calls.
3. Python code normalizes and validates those tool calls.
4. An executor handles special logic like parameter search, mission building, and mode changes.
5. The backend returns structured commands for the GCS to execute, or executes directly through MAVLink in standalone mode.
