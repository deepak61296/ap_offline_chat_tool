# Demo Videos

This folder contains demonstration videos showing the ArduPilot AI Backend in action.

## Available Demos

### demo_mavproxy_agent_mode.mkv
**Duration:** ~2 minutes
**Mode:** Agent Mode
**GCS:** MAVProxy CLI

**Demonstrates:**
- Natural language command execution in MAVProxy
- ARM command via "arm the drone"
- TAKEOFF command with altitude specification
- Movement commands (GOTO, MOVE)
- Safe mode confirmation prompts
- Real-time telemetry feedback
- LAND and DISARM sequence

**Example commands shown:**
```
ai arm the drone
ai take off to 20 meters
ai move north 50 meters
ai what's my altitude?
ai land now
```

## Upcoming Demos

The following demos are planned:

- `demo_mission_planner_script_mode.mp4` - Lua script generation and deployment
- `demo_ask_mode_telemetry.mp4` - Read-only telemetry queries
- `demo_parameter_management.mp4` - GET_PARAM and SET_PARAM workflows
- `demo_complex_missions.mp4` - Multi-step command sequences
- `demo_safety_features.mp4` - Risk validation and confirmation prompts

## How to Contribute Demos

If you have demo videos to add:

1. Record in 1080p or higher resolution
2. Keep duration under 5 minutes
3. Use descriptive filename: `demo_<mode>_<feature>.mp4`
4. Include clear audio narration or text overlay
5. Show both command input and vehicle response
6. Add entry to this README with description

## Demo Formats

Accepted video formats:
- MP4 (H.264 codec) - Recommended
- MKV (H.264 codec)
- WebM (VP9 codec)
- AVI (uncompressed, for editing source)

Maximum file size: 100MB per video (use compression if needed)

## Viewing Demos

**Linux:**
```bash
vlc demos/demo_mavproxy_agent_mode.mkv
```

**Windows:**
```bash
start demos/demo_mavproxy_agent_mode.mkv
```

**macOS:**
```bash
open demos/demo_mavproxy_agent_mode.mkv
```

## Recording Guidelines

**For MAVProxy demos:**
- Use terminal recording tool like `asciinema` for terminal-only demos
- Use screen capture (OBS Studio) for full desktop demos
- Enable MAVProxy output logging with `-v` flag
- Show backend server logs in split screen if possible

**For Mission Planner demos:**
- Record full Mission Planner window
- Show Chat Assistant panel (Ctrl+L)
- Demonstrate mode switching (Agent/Ask/Script)
- Include backend URL configuration step for first-time setup
- For Script mode, show generated Lua code and deployment

**For both:**
- Start with backend health check: `curl http://localhost:5000/health`
- Show Ollama running with `ollama list`
- Include conda environment activation
- Demonstrate error handling (e.g., backend not running)
- End with successful command execution and vehicle response
