# Comprehensive Testing Guide for ArduPilot AI Backend v3.0

## Table of Contents
1. [Setup & Prerequisites](#setup--prerequisites)
2. [Unit Tests](#unit-tests)
3. [Integration Tests](#integration-tests)
4. [Manual Testing Commands](#manual-testing-commands)
5. [Performance Testing](#performance-testing)
6. [Edge Cases & Error Handling](#edge-cases--error-handling)

---

## Setup & Prerequisites

### Start Ollama (if not running)
```bash
ollama serve
# In another terminal:
ollama pull qwen2.5:3b
```

### Activate conda environment
```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate ardupilot_ai
```

### Start the backend
```bash
cd /home/deepak/Documents/ai_backend/ardupilot-ai-backend
python run_server.py
# Should see: "ArduPilot AI Backend v3.0.0 started"
```

### Verify health endpoint
```bash
curl http://localhost:5000/health
# Should return: {"status": "healthy", "version": "3.0.0", ...}
```

---

## Unit Tests

### Run all unit tests (no server needed)
```bash
cd /home/deepak/Documents/ai_backend/ardupilot-ai-backend
python tests/test_new_tools.py
# Expected: 39 passed, 0 failed
```

### Run unit tests with verbose output
```bash
python -c "
import sys
sys.path.insert(0, '.')
from backend.tools import validate_and_coerce, extract_tool_calls, normalize_tool_call
from backend.param_db import db

# Test each function with detailed output
print('Testing validate_and_coerce...')
result = validate_and_coerce({'tool': 'takeoff', 'params': {'altitude': '25'}})
print(f'  Input: altitude as string \"25\"')
print(f'  Output: altitude as int {result[\"params\"][\"altitude\"]}')
print(f'  ✓ Type coercion works')
"
```

---

## Integration Tests

### Test 1: Health & Status Check
```bash
# Check backend is running
curl http://localhost:5000/health

# Get system status
curl http://localhost:5000/status

# Get available models
curl http://localhost:5000/models
```

### Test 2: Basic Command - ARM
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "arm the drone",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": false, "mode": "STABILIZE"},
      "battery": {"voltage": 12.5, "remaining": 85},
      "gps": {"latitude": 0, "longitude": 0, "altitude": 0, "satellites": 0}
    }
  }'
```

### Test 3: New Tool - GET_STATUS
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "how is the drone doing? what is its status?",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": true, "mode": "LOITER"},
      "battery": {"voltage": 12.1, "remaining": 45},
      "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 25.5, "satellites": 12}
    }
  }'
# Expected: Returns formatted status with battery, mode, altitude, GPS satellites
```

### Test 4: New Tool - GET_POSITION
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "where is the drone right now? give me the coordinates",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": true, "mode": "GUIDED"},
      "battery": {"voltage": 12.2, "remaining": 60},
      "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 50.0, "satellites": 15}
    }
  }'
# Expected: Returns current lat/lon/alt with satellite count
```

### Test 5: New Tool - PAUSE (Emergency Hold)
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "pause the drone hold it in place",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": true, "mode": "AUTO"},
      "battery": {"voltage": 12.0, "remaining": 50},
      "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 30.0, "satellites": 10}
    }
  }'
# Expected: Switches to LOITER mode (emergency hover)
```

### Test 6: New Tool - RESUME
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "resume the mission continue from where we stopped",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": true, "mode": "LOITER"},
      "battery": {"voltage": 12.0, "remaining": 50},
      "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 30.0, "satellites": 10}
    }
  }'
# Expected: Switches back to AUTO mode
```

### Test 7: New Tool - EXPLAIN_PARAM
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "explain what BATT_FS_LOW_VOLT does",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": false, "mode": "STABILIZE"},
      "battery": {"voltage": 12.5, "remaining": 100},
      "gps": {"latitude": 0, "longitude": 0, "altitude": 0, "satellites": 0}
    }
  }'
# Expected: Returns explanation of the battery failsafe voltage parameter
```

### Test 8: Multi-Step Mission
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "arm the drone, takeoff to 20 meters, move forward 30 meters",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": false, "mode": "STABILIZE"},
      "battery": {"voltage": 12.5, "remaining": 90},
      "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 0, "satellites": 8}
    }
  }'
# Expected: Returns multiple commands in sequence (ARM → TAKEOFF → MOVE)
```

---

## Manual Testing Commands

### Using curl with Python for pretty printing
```bash
python3 << 'CURL_TEST'
import requests
import json

BASE_URL = "http://localhost:5000"

def test_command(message, telemetry_data=None):
    """Test a command and pretty print the response."""
    if telemetry_data is None:
        telemetry_data = {
            "status": {"armed": True, "mode": "GUIDED"},
            "battery": {"voltage": 12.2, "remaining": 65},
            "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 25.5, "satellites": 12}
        }

    payload = {
        "message": message,
        "mode": "agent",
        "model": "qwen2.5:3b",
        "telemetry": telemetry_data
    }

    response = requests.post(f"{BASE_URL}/chat", json=payload)
    result = response.json()

    print(f"\n{'='*60}")
    print(f"Command: {message}")
    print(f"{'='*60}")
    print(f"Response: {result['response']}")
    if result.get('command'):
        print(f"Command Type: {result['command']['type']}")
        print(f"Command Params: {result['command']['params']}")
    print()

# Test new tools
test_command("what is the drone status?")
test_command("where am I located right now?")
test_command("pause the drone hold position")
test_command("resume the mission")
test_command("what does BATT_CRT_VOLT parameter do?")
CURL_TEST
```

---

## Performance Testing

### Test 1: Response Time (Single Command)
```bash
python3 << 'PERF_TEST'
import requests
import time
import json

BASE_URL = "http://localhost:5000"

commands = [
    "arm the drone",
    "takeoff to 20 meters",
    "what is the status?",
    "where is the drone?",
    "explain BATT_FS_LOW_VOLT"
]

print("Response Time Test")
print("=" * 50)

for cmd in commands:
    payload = {
        "message": cmd,
        "mode": "agent",
        "model": "qwen2.5:3b",
        "telemetry": {
            "status": {"armed": True, "mode": "GUIDED"},
            "battery": {"voltage": 12.2, "remaining": 65},
            "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 25.5, "satellites": 12}
        }
    }

    start = time.time()
    response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
    elapsed = time.time() - start

    result = response.json()
    status = "✓" if result['success'] else "✗"
    print(f"{status} '{cmd[:30]:30s}' - {elapsed:.2f}s")
PERF_TEST
```

### Test 2: Stress Test (Multiple Rapid Commands)
```bash
python3 << 'STRESS_TEST'
import requests
import concurrent.futures
import time

BASE_URL = "http://localhost:5000"

def send_command(cmd_num):
    payload = {
        "message": f"command {cmd_num}",
        "mode": "ask",
        "model": "qwen2.5:3b",
        "telemetry": {
            "status": {"armed": True, "mode": "GUIDED"},
            "battery": {"voltage": 12.2, "remaining": 65},
            "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 25.5, "satellites": 12}
        }
    }

    start = time.time()
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
        elapsed = time.time() - start
        success = response.status_code == 200
        return (cmd_num, success, elapsed)
    except Exception as e:
        return (cmd_num, False, time.time() - start)

print("Stress Test: 20 parallel requests")
print("=" * 50)

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    start = time.time()
    results = list(executor.map(send_command, range(20)))
    total_time = time.time() - start

successful = sum(1 for _, success, _ in results if success)
avg_time = sum(t for _, _, t in results) / len(results)

print(f"Total time: {total_time:.2f}s")
print(f"Successful: {successful}/20")
print(f"Average response time: {avg_time:.2f}s")
STRESS_TEST
```

---

## Edge Cases & Error Handling

### Test 1: Invalid JSON
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
# Expected: Error response
```

### Test 2: Missing Message Field
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "agent",
    "model": "qwen2.5:3b"
  }'
# Expected: {"success": false, "error": "Missing message"}
```

### Test 3: Empty Message
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {}
  }'
# Expected: Error about empty message
```

### Test 4: Disarmed Drone Takeoff (Should auto-arm)
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "takeoff to 15 meters",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": false, "mode": "STABILIZE"},
      "battery": {"voltage": 12.5, "remaining": 85},
      "gps": {"latitude": 0, "longitude": 0, "altitude": 0, "satellites": 0}
    }
  }'
# Expected: Auto-injects ARM before TAKEOFF
```

### Test 5: No GPS Data (GET_POSITION should handle gracefully)
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "where am I?",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": false, "mode": "STABILIZE"},
      "battery": {"voltage": 12.5, "remaining": 85},
      "gps": {"latitude": 0, "longitude": 0, "altitude": 0, "satellites": 0}
    }
  }'
# Expected: Graceful message about GPS not available
```

### Test 6: Parameter Not Found
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "explain NONEXISTENT_PARAM_XYZ",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": false, "mode": "STABILIZE"},
      "battery": {"voltage": 12.5, "remaining": 85},
      "gps": {"latitude": 0, "longitude": 0, "altitude": 0, "satellites": 0}
    }
  }'
# Expected: Graceful message about parameter not found
```

### Test 7: Invalid Flight Mode
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "switch to INVALID_MODE_XYZ",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": {
      "status": {"armed": true, "mode": "GUIDED"},
      "battery": {"voltage": 12.2, "remaining": 65},
      "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 25.5, "satellites": 12}
    }
  }'
# Expected: Error about invalid mode
```

### Test 8: Malformed Telemetry
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "arm",
    "mode": "agent",
    "model": "qwen2.5:3b",
    "telemetry": "invalid"
  }'
# Expected: Graceful handling
```

---

## Deep Dive Testing

### Test Tool Extraction (No Server Needed)
```bash
python3 << 'EXTRACTION_TEST'
import sys
sys.path.insert(0, '.')
from backend.tools import extract_tool_calls, normalize_tool_call

test_cases = [
    # (response, expected_tool_count, expected_types)
    ('```json\n[{"tool":"arm"}]\n```', 1, ["ARM"]),
    ('```json\n[{"tool":"arm"},{"tool":"takeoff","params":{"altitude":20}}]\n```', 2, ["ARM", "TAKEOFF"]),
    ('Let me arm it: {"tool":"arm"}', 1, ["ARM"]),
    ('[{"tool":"land"}]', 1, ["LAND"]),
    ('No JSON here', 0, []),
]

print("Tool Extraction Test")
print("=" * 60)

for response, exp_count, exp_types in test_cases:
    text, calls = extract_tool_calls(response)
    actual_types = [normalize_tool_call(c)["type"] for c in calls if normalize_tool_call(c)]

    status = "✓" if len(calls) == exp_count and actual_types == exp_types else "✗"
    print(f"{status} Extracted {len(calls)} tools: {actual_types}")
    if status == "✗":
        print(f"   Expected: {exp_count} tools with types {exp_types}")
EXTRACTION_TEST
```

### Test Parameter Search Accuracy
```bash
python3 << 'PARAM_TEST'
import sys
sys.path.insert(0, '.')
from backend.param_db import db

queries = [
    ("battery failsafe", "BATT_FS"),
    ("motor spin", "MOT_SPIN"),
    ("loiter", "LOIT_"),
    ("gps accuracy", "GPS_"),
    ("compass calibration", "COMPASS_"),
    ("arming check", "ARMING_"),
]

print("Parameter Search Accuracy Test")
print("=" * 60)

for query, expected_prefix in queries:
    results = db.search(query, top_k=1)
    if results:
        param_name = results[0]["name"]
        status = "✓" if param_name.startswith(expected_prefix) else "⚠"
        print(f"{status} '{query:25s}' -> {param_name}")
    else:
        print(f"✗ '{query:25s}' -> NO RESULTS")
PARAM_TEST
```

### Test Validation & Coercion
```bash
python3 << 'VALIDATION_TEST'
import sys
sys.path.insert(0, '.')
from backend.tools import validate_and_coerce

test_cases = [
    # (input, should_be_valid, expected_key_type)
    ({"tool": "takeoff", "params": {"altitude": "25"}}, True, int),
    ({"tool": "set_speed", "params": {"speed": "5.5"}}, True, float),
    ({"tool": "arm", "confidence": 0.95}, True, None),
    ({"tool": "FAKE_TOOL"}, False, None),
    ({"tool": "arm", "params": None}, True, None),
]

print("Validation & Coercion Test")
print("=" * 60)

for input_data, should_be_valid, expected_type in test_cases:
    result = validate_and_coerce(input_data)
    is_valid = result is not None
    status = "✓" if is_valid == should_be_valid else "✗"

    if expected_type and is_valid:
        first_param = list(result.get("params", {}).values())[0] if result.get("params") else None
        actual_type = type(first_param).__name__
        type_match = isinstance(first_param, expected_type) if first_param else True
        print(f"{status} {input_data['tool']:20s} - Valid:{is_valid}, Type: {actual_type}")
    else:
        print(f"{status} {input_data['tool']:20s} - Valid:{is_valid}")
VALIDATION_TEST
```

---

## Running Full Test Suite

### All tests in one go
```bash
cd /home/deepak/Documents/ai_backend/ardupilot-ai-backend

echo "1. Running unit tests..."
python tests/test_new_tools.py

echo -e "\n2. Health check..."
curl -s http://localhost:5000/health | python -m json.tool

echo -e "\n3. Parameter search accuracy..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from backend.param_db import db
results = db.search("battery failsafe", 3)
for r in results:
    print(f"  - {r['name']}")
EOF
```

---

## Verification Checklist

- [ ] All 39 unit tests pass
- [ ] GET_STATUS returns correct telemetry format
- [ ] GET_POSITION handles no-GPS gracefully
- [ ] PAUSE switches to LOITER mode
- [ ] RESUME switches to AUTO mode
- [ ] EXPLAIN_PARAM finds correct parameter
- [ ] Invalid tools are filtered out
- [ ] Type coercion works (string "25" → int 25)
- [ ] Multi-step commands execute in order
- [ ] Parameter search deprioritizes SIM_ params
- [ ] Backend responds to all 20+ tools
- [ ] Error messages are helpful
- [ ] Performance: <2s response time for simple commands

