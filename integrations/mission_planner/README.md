# Mission Planner AI Assistant Plugin

Chat-based drone control for Mission Planner.

## Installation

### Option 1: Use Pre-built Release

Download from [Mission Planner fork releases](https://github.com/deepak61296/MissionPlanner/releases) and run.

### Option 2: Build from Source

1. Clone Mission Planner fork:
```bash
git clone https://github.com/deepak61296/MissionPlanner.git
cd MissionPlanner
git checkout feature/script-mode-clean
```

2. Copy plugin files (if updating):
```bash
cp ChatAssistant.cs GCSViews/
cp DroneCommandExecutor.cs .
```

3. Build with Visual Studio or:
```bash
dotnet build MissionPlanner.csproj
```

## Usage

1. Start backend server
2. Open Mission Planner
3. Connect to vehicle
4. Click "AI Chat" button in toolbar
5. Type natural language commands

## Features

- **Agent Mode**: Execute commands (arm, takeoff, land, etc.)
- **Ask Mode**: Read-only telemetry queries
- **Script Mode**: Generate and flash Lua scripts to flight controller

## Configuration

Right-click the connection button to set backend URL (default: http://localhost:5000).

## Examples

**Agent Mode:**
```
arm the drone
takeoff to 15 meters
move north 30 meters
set speed to 5 m/s
return home
```

**Ask Mode:**
```
what's my battery voltage?
how many GPS satellites?
what altitude am I at?
```

**Script Mode:**
```
create a script to monitor battery and RTL below 20%
generate a script to print roll and pitch every 3 seconds
write a script to circle around home at 50m
```

## Requirements

- Mission Planner (Windows/Linux)
- .NET Framework 4.8+ or .NET 6.0+
- Backend server running

## Notes

Scripts are automatically saved and can be flashed to `/APM/scripts/` via MAVFTP.

Version: Compatible with backend v2.3.0+
