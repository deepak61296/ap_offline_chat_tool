# Contributing

## Repository Structure

This project spans 3 repositories:

| Repo | Purpose | Branch |
|------|---------|--------|
| [ardupilot-ai-backend](https://github.com/deepak61296/ardupilot-ai-backend) | Core backend + integration copies | `feature/modular-gcs-backend` |
| [MAVProxy fork](https://github.com/deepak61296/MAVProxy) | MAVProxy with AI module | `feature/ai-backend-integration` |
| [MissionPlanner fork](https://github.com/deepak61296/MissionPlanner) | Mission Planner with chat UI | `feature/script-mode-clean` |

The main repo (`ardupilot-ai-backend`) contains copies of integration files in `integrations/`. The forks contain the actual working code.

## Development Setup

### Backend

```bash
git clone https://github.com/deepak61296/ardupilot-ai-backend.git
cd ardupilot-ai-backend
conda create -n ai_backend python=3.10 -y
conda activate ai_backend
pip install -r requirements.txt

# Start
ollama serve              # Terminal 1
python -m backend.api_server  # Terminal 2
```

### MAVProxy

```bash
git clone https://github.com/deepak61296/MAVProxy.git
cd MAVProxy
git checkout feature/ai-backend-integration
pip install -e .

# Test with SITL
mavproxy.py --master=udp:127.0.0.1:14550 --console
module load ai_backend
ai_backend enable
```

### Mission Planner

```bash
git clone https://github.com/deepak61296/MissionPlanner.git
cd MissionPlanner
git checkout feature/script-mode-clean
dotnet build MissionPlanner.csproj
```

## How to Add a New Command

### 1. Backend - Add Trigger Phrase

Edit `backend/prompts.py` and add the phrase the AI should use:
```python
# In AGENT_MODE_PROMPT, add to command examples:
- "your command" → "Your exact response phrase."
```

Also add it to the list of exact phrases (section 7).

### 2. Backend - Add Extraction Logic

Edit `backend/commands.py`:
```python
def extract_your_command(ai_response: str):
    response_lower = ai_response.lower()
    match = re.search(r'your pattern here (\d+)', response_lower)
    if match:
        value = float(match.group(1))
        return {"type": "YOUR_COMMAND", "params": {"value": value}}
    return None
```

Call it from `extract_command()`:
```python
cmd = extract_your_command(ai_response)
if cmd:
    return cmd
```

### 3. Backend - Add Validation

In `commands.py`, add to `validate_command()`:
```python
elif cmd_type == "YOUR_COMMAND":
    value = params.get("value", 0)
    if value > MAX_LIMIT:
        return False, "Value exceeds limit"
```

### 4. Backend - Add Risk Level

In `config.py`:
```python
COMMAND_RISK_LEVELS = {
    ...
    "YOUR_COMMAND": "medium",  # low, medium, high, critical
}
```

### 5. MAVProxy Module - Add Execution

Edit `integrations/mavproxy/mavproxy_ai_backend.py`:

In `format_command()`:
```python
elif cmd_type == "YOUR_COMMAND":
    value = params.get('value', 0)
    return f"YOUR_CMD {value}"
```

In `execute_command()`:
```python
elif cmd_type == "YOUR_COMMAND":
    value = params.get('value', 0)
    self.master.mav.command_long_send(
        self.target_system, self.target_component,
        mavutil.mavlink.MAV_CMD_YOUR_COMMAND,
        0, value, 0, 0, 0, 0, 0, 0
    )
    print(f"AI Backend: YOUR_COMMAND sent")
```

### 6. Test It

```bash
# Start backend + SITL + MAVProxy
# Type your natural language command
# Check backend terminal for extraction
# Check MAVProxy for execution
```

## How to Add a New GCS Integration

1. Create `integrations/your_gcs/` folder
2. Implement HTTP client that calls `POST /chat`
3. Parse the JSON response and extract `command`
4. Execute the command via MAVLink
5. Add README with installation steps

### API Contract

**Request:**
```json
POST /chat
{
    "message": "arm the drone",
    "mode": "agent",
    "telemetry": {
        "battery": {"voltage": 12.4, "remaining": 87},
        "gps": {"latitude": 37.77, "longitude": -122.41, "satellites": 12},
        "status": {"mode": "STABILIZE", "armed": false},
        "position": {"relative_altitude": 0.0}
    }
}
```

**Response:**
```json
{
    "success": true,
    "response": "Arming the drone now.",
    "command": {
        "type": "ARM",
        "params": {}
    },
    "mode": "agent",
    "model": "qwen2.5:3b"
}
```

## Syncing Integration Copies

After making changes in a fork, copy the updated files back to the main repo:

```bash
# MAVProxy
cp MAVProxy/modules/mavproxy_ai_backend.py ardupilot-ai-backend/integrations/mavproxy/

# Mission Planner
cp MissionPlanner/GCSViews/ChatAssistant.cs ardupilot-ai-backend/integrations/mission_planner/
cp MissionPlanner/GCSViews/ChatAssistant.Designer.cs ardupilot-ai-backend/integrations/mission_planner/GCSViews/
cp MissionPlanner/GCSViews/FlightData.cs ardupilot-ai-backend/integrations/mission_planner/GCSViews/
cp MissionPlanner/GCSViews/ConfigurationView/ConfigRawParams.cs ardupilot-ai-backend/integrations/mission_planner/GCSViews/ConfigurationView/
cp MissionPlanner/AIBackendService.cs ardupilot-ai-backend/integrations/mission_planner/
cp MissionPlanner/DroneCommandExecutor.cs ardupilot-ai-backend/integrations/mission_planner/
```

Update `COMPATIBILITY.md` with new commit hashes.

## Commit Guidelines

- Keep messages short (1-2 lines)
- Use lowercase
- Describe what changed, not how
- Examples:
  ```
  add speed command support
  fix altitude change param mismatch
  update mavproxy module to v2.3
  ```

## Running Tests

```bash
conda activate ai_backend
python -m pytest tests/test_comprehensive.py -v
```

## Reporting Issues

Open an issue at https://github.com/deepak61296/ardupilot-ai-backend/issues with:
- What you tried
- What happened
- Backend terminal output
- GCS version and branch
