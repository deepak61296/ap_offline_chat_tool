# Version Compatibility

Track which versions of forks work with which backend versions.

## Current Versions

| Component | Version/Commit | Status |
|-----------|---------------|---------|
| Backend | v2.3.0 | Latest |
| MAVProxy Module | 20749836 | Latest |
| Mission Planner Plugin | 58b3e91cb | Latest |

## Version Matrix

| Backend | MAVProxy | Mission Planner | Notes |
|---------|----------|-----------------|-------|
| v2.3.0 | 20749836 | 58b3e91cb | Added SET_SPEED, SET_YAW commands |
| v2.2.1 | fbf7fa2c | - | Fixed prompt updates, mode changes |
| v2.2.0 | a423ecb7 | - | Input handler, direct MAVLink |
| v2.1.0 | a9a1508c | - | MOVE_DIRECTION, ALTITUDE_CHANGE |
| v2.0.0 | 3f16ecbe | - | Initial AI backend module |

## Installation

### Backend
```bash
git clone https://github.com/deepak61296/ardupilot-ai-backend.git
cd ardupilot-ai-backend
git checkout feature/modular-gcs-backend  # Latest
conda create -n ardupilot_ai python=3.10
conda activate ardupilot_ai
pip install -r requirements.txt
python -m backend.api_server
```

### MAVProxy Integration
```bash
git clone https://github.com/deepak61296/MAVProxy.git
cd MAVProxy
git checkout feature/ai-backend-integration
git reset --hard 20749836  # Pin to compatible version
pip install -e .

# Copy module
cp MAVProxy/modules/mavproxy_ai_backend.py ~/.local/lib/python3.11/site-packages/MAVProxy/modules/
```

### Mission Planner Integration

**Option 1 - Use release:**
Download from https://github.com/deepak61296/MissionPlanner/releases

**Option 2 - Build from source:**
```bash
git clone https://github.com/deepak61296/MissionPlanner.git
cd MissionPlanner
git checkout feature/script-mode-clean
git reset --hard 58b3e91cb  # Pin to compatible version
dotnet build MissionPlanner.csproj
```

## Fork Repositories

| Fork | URL | Branch |
|------|-----|--------|
| MAVProxy | https://github.com/deepak61296/MAVProxy | feature/ai-backend-integration |
| Mission Planner | https://github.com/deepak61296/MissionPlanner | feature/script-mode-clean |

## Breaking Changes

### v2.3.0
- Fixed param key mismatches (ALTITUDE_CHANGE, GET/SET_PARAM)
- MAVProxy module must be updated to match

### v2.2.0
- Changed to input_handler approach
- Old unknown_command() hook no longer used

### v2.0.0
- Initial release
- Requires MAVProxy fork with custom module support

## Testing Compatibility

After updating:

1. **Backend health check:**
```bash
curl http://localhost:5000/health
```

2. **MAVProxy test:**
```
module load ai_backend
ai_backend enable
ai_backend status
```

3. **End-to-end test:**
```
arm the drone
# Should see "AI Backend: ARM command sent"
```

## Reporting Issues

If versions don't work together:
1. Check commit hashes match this table
2. Verify backend is running (`/health` endpoint)
3. Check MAVProxy module loaded (`ai_backend status`)
4. Open issue with version info and logs

## Update Frequency

- Backend: Active development
- MAVProxy fork: Synced with upstream monthly
- Mission Planner fork: Synced with upstream monthly
