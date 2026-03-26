# Mission Planner AI Assistant Plugin

Chat-based drone control for Mission Planner.

[![Mission Planner Demo](https://img.youtube.com/vi/mMeY41tOgTs/0.jpg)](https://www.youtube.com/watch?v=mMeY41tOgTs)

## Files

All files needed for AI integration:

| File | Type | Description |
|------|------|-------------|
| `GCSViews/ChatAssistant.cs` | Modified | Main chat UI (agent/ask/script modes) |
| `GCSViews/ChatAssistant.Designer.cs` | Modified | Auto-generated UI layout |
| `GCSViews/FlightData.cs` | Modified | Adds AI Chat button to flight data |
| `GCSViews/ConfigurationView/ConfigRawParams.cs` | Modified | Backend URL configuration |
| `AIBackendService.cs` | Modified | HTTP service for backend communication |
| `DroneCommandExecutor.cs` | New | MAVLink command execution from AI responses |
| `csproj.patch` | Patch | Build fix for Plugins folder casing |
| `start_script_mode_testing.ps1` | New | Script mode test helper |

## Installation

### Option 1: Use Pre-built Release

Download from [Mission Planner fork releases](https://github.com/deepak61296/MissionPlanner/releases) and run.

### Option 2: Build from Source

**Important Branch Info:**
The Mission Planner fork relies on specific feature branches.
- **Default branch:** `feature/ai-chat-assistant` (Older version)
- **Feature branch:** `feature/script-mode-clean` (Latest stable AI features)

1. Clone Mission Planner fork and checkout the correct branch:
```bash
git clone https://github.com/deepak61296/MissionPlanner.git
cd MissionPlanner
git checkout feature/script-mode-clean
```

2. Build:
```bash
dotnet build MissionPlanner.csproj
```

### Option 3: Apply to Existing MP

If you already have MP source:

1. Copy modified files to matching paths in your MP repo
2. Apply the csproj patch: `git apply csproj.patch`
3. Build

## Usage

1. Start backend server
2. Open Mission Planner
3. Connect to vehicle
4. Click "AI Chat" button in flight data view
5. Type natural language commands

## Features

- **Agent Mode**: Execute commands (arm, takeoff, land, etc.)
- **Ask Mode**: Read-only telemetry queries
- **Script Mode**: Generate and flash Lua scripts to flight controller via MAVFTP

## Configuration

Right-click the connection button to set backend URL (default: http://localhost:5000).

## Requirements

- Mission Planner (Windows/Linux)
- .NET Framework 4.8+ or .NET 6.0+
- Backend server running

## Notes

Scripts are saved locally and can be flashed to `/APM/scripts/` via MAVFTP. The module creates the directory on the flight controller if it doesn't exist (works with both real hardware and SITL).

Version: Compatible with backend v2.3.0+
