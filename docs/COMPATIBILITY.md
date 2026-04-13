# Compatibility

This file documents what the current code expects. It does not pin external fork commits.

## Python dependencies

From `requirements.txt`:

- `flask`
- `flask-cors`
- `ollama`
- `requests`
- `pymavlink` optional, for standalone mode
- `rich`

## Runtime assumptions

- backend listens on `http://localhost:5000` unless code is changed
- Ollama is reachable at `OLLAMA_HOST`, default `http://localhost:11434`
- integrated mode expects the client to send telemetry and execute returned commands
- standalone mode expects `pymavlink` and a valid connection string

## Integration contract

Included client code assumes:

- `GET /health` returns `status: healthy`
- `GET /status` returns backend status JSON
- `POST /chat` accepts `message`, `mode`, optional `model`, optional `telemetry`
- command payloads use the shape `{ "type": "...", "params": { ... } }`

## Known mismatches inside the repo

- `backend/executor.py` emits `ALTITUDE_CHANGE` with param key `change` when normalized from tool calls
- `integrations/mission_planner/DroneCommandExecutor.cs` expects `ALTITUDE_CHANGE` param key `altitude_change`

That mismatch exists in code today and is not resolved by docs.
