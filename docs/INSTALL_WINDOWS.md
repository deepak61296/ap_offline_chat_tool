# Windows Setup

## Requirements

- Python 3.10+
- Ollama
- optional: `pymavlink` for standalone mode

## Install

```powershell
git clone https://github.com/deepak61296/ardupilot-ai-backend.git
cd ardupilot-ai-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
ollama pull qwen2.5:3b
```

## Run

Integrated mode:

```powershell
python run_server.py
```

Standalone mode with direct MAVLink:

```powershell
python run_server.py --standalone --connect COM3 --baud 57600
```

CPU-only or lower-context startup:

```powershell
python run_server.py --no-gpu
python run_server.py --low-power
```

## Smoke checks

```powershell
curl http://localhost:5000/health
curl http://localhost:5000/status
curl http://localhost:5000/models
```

Agent request:

```powershell
curl -X POST http://localhost:5000/chat `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"arm the drone\",\"mode\":\"agent\"}"
```

Ask request:

```powershell
curl -X POST http://localhost:5000/chat `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"what mode am I in?\",\"mode\":\"ask\",\"telemetry\":{\"status\":{\"mode\":\"LOITER\"}}}"
```
