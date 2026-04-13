# Mission Planner Integration

This repo includes Mission Planner-side integration files under `integrations/mission_planner/`.

## Files

- `AIBackendService.cs`: HTTP client for `/health`, `/status`, `/chat`
- `DroneCommandExecutor.cs`: executes returned commands through Mission Planner MAVLink APIs
- `ChatAssistant.cs`: UI layer

## Backend contract used by `AIBackendService.cs`

Request:

```json
{
  "message": "takeoff to 10 meters",
  "mode": "agent",
  "model": "qwen2.5:3b",
  "telemetry": {}
}
```

Response shape expected by the client:

```json
{
  "success": true,
  "response": "Taking off to 10 meters.",
  "command": {
    "type": "TAKEOFF",
    "params": {
      "altitude": 10
    }
  },
  "mode": "agent",
  "model": "qwen2.5:3b",
  "error": null
}
```

## Commands implemented in `DroneCommandExecutor.cs`

- `ARM`
- `DISARM`
- `TAKEOFF`
- `LAND`
- `RTL`
- `REBOOT`
- `CHANGE_MODE`
- `GOTO`
- `ALTITUDE_CHANGE`
- `GOTO_HOME`
- `MOVE_DIRECTION`
- `GET_PARAM`
- `SET_PARAM`
- `LUA_SCRIPT`

The backend supports additional command types beyond that list. If the backend starts returning new command types to Mission Planner, `DroneCommandExecutor.cs` must be updated.
