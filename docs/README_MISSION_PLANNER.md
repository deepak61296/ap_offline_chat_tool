# ArduPilot AI Backend - Mission Planner Integration

HTTP API wrapper for integrating AI chat capabilities with Mission Planner.

## Overview

This branch contains the AI backend API server that enables natural language interaction with ArduPilot drones through Mission Planner.

**Features:**
- Natural language command parsing (ARM, DISARM, TAKEOFF, LAND, RTL)
- Qwen 2.5 AI model integration via Ollama
- Flask HTTP API for Mission Planner communication
- Command detection and structured JSON responses

## Architecture

```
Mission Planner (C#) <--HTTP--> API Server (Python) <--> Ollama (Qwen 2.5)
```

## Installation

### Prerequisites

1. **Miniconda** (Python 3.10)
2. **Ollama** (v0.13.5+)
3. **AI Model**: qwen2.5:3b

### Setup Steps

1. **Create Conda Environment**
   ```bash
   conda create -n ai_backend python=3.10
   conda activate ai_backend
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install flask flask-cors ollama
   ```

3. **Install Ollama and Pull Model**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull qwen2.5:3b
   ```

## Usage

### Start API Server

```bash
conda activate ai_backend
python api_server.py
```

Server will run on `http://localhost:5000`

### API Endpoints

#### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "ArduPilot AI Backend",
  "version": "1.0.0",
  "model": "qwen2.5:3b"
}
```

#### `GET /status`
Get backend status and model information

**Response:**
```json
{
  "status": "running",
  "model": "qwen2.5:3b",
  "backend": "Ollama",
  "model_available": true,
  "connection": "ready",
  "features": ["command_parsing", "natural_language"]
}
```

#### `POST /chat`
Send message and get AI response with optional command

**Request:**
```json
{
  "message": "takeoff to 10 meters"
}
```

**Response:**
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
  "error": null
}
```

## Supported Commands

| Command | Example | Parameters |
|---------|---------|------------|
| ARM | "arm the drone" | None |
| DISARM | "disarm" | None |
| TAKEOFF | "takeoff to 10 meters" | altitude (meters) |
| LAND | "land the drone" | None |
| RTL | "return to launch" | None |

## Command Detection

The API server uses regex patterns to detect commands in AI responses:

```python
# ARM command
r'\b(arm|arming)\b'

# TAKEOFF command with altitude
r'(?:takeoff|take off|taking off).*?(\d+)\s*(?:meters|m\b)'

# LAND command
r'\b(land|landing)\b'

# RTL command
r'\b(rtl|return to launch|return home)\b'
```

## Configuration

### Model Selection

Edit `api_server.py`:
```python
MODEL_NAME = 'qwen2.5:3b'  # Change to qwen2.5:7b or other models
```

### Port Configuration

Default port: `5000`

To change:
```python
app.run(host='0.0.0.0', port=5000)  # Change port here
```

## Development

### Project Structure

```
ardupilot-ai-backend/
 api_server.py          # Main Flask API server
 requirements.txt       # Python dependencies
 src/
    function_gemma.py  # Original AI backend (not used in wrapper)
 examples/
     demo.py            # Standalone demo
```

### Adding New Commands

1. Add regex pattern to `extract_command()` function
2. Define command type and parameters
3. Update Mission Planner's `DroneCommandExecutor.cs`

Example:
```python
# In extract_command()
if re.search(r'\bchange altitude to (\d+)', response_lower):
    altitude = int(match.group(1))
    return {"type": "CHANGE_ALT", "params": {"altitude": altitude}}
```

## Testing

### Test API Server

```bash
# Health check
curl http://localhost:5000/health

# Status check
curl http://localhost:5000/status

# Send chat message
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "arm the drone"}'
```

### Expected Responses

**Simple chat:**
```json
{
  "success": true,
  "response": "Hello! How can I help you?",
  "command": null,
  "error": null
}
```

**Command detected:**
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

## Integration with Mission Planner

See Mission Planner repository for C# integration code:
- `AIBackendService.cs` - HTTP client
- `DroneCommand.cs` - Command data structures
- `DroneCommandExecutor.cs` - MAVLink execution
- `ChatAssistant.cs` - UI integration

## Troubleshooting

### Server Won't Start

**Issue**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
conda activate ai_backend
pip install flask flask-cors
```

### Model Not Found

**Issue**: `Model qwen2.5:3b not found`

**Solution**:
```bash
ollama pull qwen2.5:3b
```

### Slow First Response

**Normal**: First query loads model into memory (20-30s)
Subsequent queries are faster (2-5s)

## Performance

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| qwen2.5:3b | 2GB | Fast (2-5s) | Good |
| qwen2.5:7b | 4.7GB | Medium (5-10s) | Better |
| qwen2.5:14b | 9GB | Slow (10-20s) | Best |

## License

Same as parent ArduPilot project

## Contributing

1. Create feature branch from `mission-planner-integration`
2. Make changes
3. Test with Mission Planner
4. Submit pull request

## Contact

For issues related to Mission Planner integration, see main Mission Planner repository.