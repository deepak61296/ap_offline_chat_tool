# MAVProxy AI Backend Module

Natural language control for MAVProxy.

[![MAVProxy Demo](https://img.youtube.com/vi/8ATi4Uj1ndc/0.jpg)](https://www.youtube.com/watch?v=8ATi4Uj1ndc)

## Installation

**Important Branch Info:**
If you are cloning the MAVProxy fork, note that the default branch is `master`. The AI Backend features are on the `feature/ai-backend-integration` branch.

### Option 1: Drop-in Module
Copy `mavproxy_ai_backend.py` to your MAVProxy modules folder:

**Windows:**
```bash
copy mavproxy_ai_backend.py %USERPROFILE%\AppData\Local\MAVProxy\modules\
```

**Linux/Mac:**
```bash
cp mavproxy_ai_backend.py ~/.local/lib/python3.*/site-packages/MAVProxy/modules/
```

## Usage

Start MAVProxy and load the module:
```
module load ai_backend
ai_backend enable
```

Now you can use natural language:
```
arm the drone
takeoff to 10 meters
move north 20 meters
land
```

## Configuration

Set backend URL (default: http://localhost:5000):
```
ai_backend url http://192.168.1.100:5000
```

Enable safe mode (requires y/n confirmation):
```
ai_backend safe
```

## Commands

- `ai_backend enable` - Enable natural language processing
- `ai_backend disable` - Disable module
- `ai_backend status` - Show connection status
- `ai_backend url <URL>` - Set backend URL
- `ai_backend safe` - Enable confirmation prompts
- `ai_backend unsafe` - Disable confirmations

## Requirements

- MAVProxy 1.8.0+
- Python `requests` library
- Backend server running

## Files

| File | Description |
|------|-------------|
| `mavproxy_ai_backend.py` | Main module (drop into MAVProxy modules folder) |
| `mavproxy_ai_flag.patch` | Optional patch to add `--ai-backend` flag to mavproxy.py |

The patch adds `--ai-backend` CLI flag for auto-loading the module on startup:
```bash
mavproxy.py --master=udp:127.0.0.1:14550 --ai-backend
```

Without the patch, just load manually:
```
module load ai_backend
ai_backend enable
```

## Notes

Module intercepts input before MAVProxy processes it. Regular MAVProxy commands still work normally.

Version: 2.3.0
