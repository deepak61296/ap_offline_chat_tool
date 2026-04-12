# QGroundControl AI Backend Integration

This document describes how to integrate the cleaned two-mode ArduPilot AI Backend with QGroundControl.

## Overview

The AI Backend provides natural language control for ArduPilot drones through QGroundControl. Users can:
- **Ask Mode**: Query telemetry data and get information about the drone
- **Agent Mode**: Execute commands using natural language (arm, takeoff, land, etc.)

[![QGroundControl Demo](https://img.youtube.com/vi/J89E-0sYJxw/0.jpg)](https://www.youtube.com/watch?v=J89E-0sYJxw)

## Requirements

1. **ArduPilot AI Backend** running on `http://localhost:5000`
2. **Ollama** with `qwen2.5:3b` model installed
3. **QGroundControl fork repository**
   - **Default branch:** `master`
   - **Feature branch:** `feature/ai-backend-integration` (You *must* checkout this branch for the AI features)

Note: this repo only contains the backend-side contract and integration notes for QGroundControl. The QGroundControl source files listed below live in the QGroundControl fork, not in this backend repo.

## Setup

### 1. Start the AI Backend

```bash
cd ardupilot-ai-backend
conda activate ardupilot_ai
python -m backend.api_server
```

### 2. Enable AI in QGroundControl

1. Open QGroundControl
2. Go to **Application Settings**
3. Enable **AI Backend**
4. Configure:
   - **Backend URL**: `http://localhost:5000` (default)
   - **Mode**: Ask (read-only) or Agent (execute commands)
   - **Model**: Select from available Ollama models

### 3. Use the Chat Panel

- Press **Ctrl+L** to toggle the AI chat panel (works in FlyView and PlanView)
- Type messages in natural language
- View AI responses and executed commands

## API Integration

### Chat Endpoint

QGroundControl sends requests to `POST /chat`:

```json
{
    "message": "arm the drone",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
        "battery": {"voltage": 12.4, "remaining": 85},
        "gps": {"latitude": 0.0, "longitude": 0.0, "altitude": 10.0, "satellites": 12},
        "status": {"mode": "GUIDED", "armed": false},
        "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 90.0},
        "speed": {"ground_speed": 0.0, "climb_rate": 0.0}
    }
}
```

### Response Format

```json
{
    "success": true,
    "response": "Arming the drone now.",
    "command": {
        "type": "ARM",
        "params": {}
    },
    "error": null
}
```

## Supported Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| ARM | Arm the drone | - |
| DISARM | Disarm the drone | - |
| TAKEOFF | Take off to altitude | `altitude` (meters) |
| LAND | Land the drone | - |
| RTL | Return to launch | - |
| CHANGE_MODE | Change flight mode | `mode` (string) |
| GOTO | Go to location | `latitude`, `longitude`, `altitude` |

## Safety Notes

- **Ask Mode** is read-only and safe for all users
- **Agent Mode** executes commands - use with caution
- Always have manual override ready
- Test in simulation before real flights

## Telemetry Data

The following telemetry is sent with each request:

- **Battery**: voltage, remaining percentage
- **GPS**: latitude, longitude, altitude, satellites
- **Status**: flight mode, armed state
- **Attitude**: roll, pitch, yaw
- **Speed**: ground speed, climb rate

## Troubleshooting

### Connection Failed
- Verify backend is running: `curl http://localhost:5000/health`
- Check firewall settings
- Ensure Ollama is running: `curl http://localhost:11434/api/tags`

### No Models Available
- Pull default model: `ollama pull qwen2.5:3b`
- Restart QGroundControl after pulling models

### Commands Not Executing
- Ensure Agent mode is selected
- Check vehicle is connected in QGroundControl
- Verify vehicle is ready to receive commands

## Files Modified in QGroundControl

```
src/AI/
├── AIChatController.h      # C++ controller
├── AIChatController.cc     # Implementation
├── AIChatPanel.qml         # UI component
└── CMakeLists.txt          # Build config

src/Settings/
├── App.SettingsGroup.json  # AI settings definitions
└── AppSettings.h           # Settings macros

src/UI/
└── MainWindow.qml          # Ctrl+L shortcut + panel

src/CMakeLists.txt          # Added AI subdirectory
```
