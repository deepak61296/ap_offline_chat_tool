# Docker Testing Guide

## Quick Docker Tests

This guide shows how to test the Docker container to ensure everything works correctly.

## Prerequisites

- Docker installed and running
- Project cloned locally

## Build the Container

```bash
# Navigate to project directory
cd ap_offline_chat_tool

# Build the Docker image
docker build -t ap_offline_chat_tool .

# Verify image was created
docker images | grep ap_offline_chat_tool
```

Expected output:
```
ap_offline_chat_tool   latest    <image_id>   <time>   ~1.5GB
```

## Run Tests

### 1. Test Suite (20 tests)

```bash
docker run --rm ap_offline_chat_tool python3 tests/test_suite.py
```

**Expected Output:**
```
============================================================
TEST SUMMARY
============================================================
Total Tests: 20
[PASS] Passed: 20
[FAIL] Failed: 0
Success Rate: 100.0%
============================================================

🎉 ALL TESTS PASSED! 🎉
```

### 2. Preprocessing Tests (11 tests)

```bash
docker run --rm ap_offline_chat_tool python3 tests/test_preprocessing.py
```

**Expected Output:**
```
============================================================
TESTING COMMAND PREPROCESSING
============================================================

[PASS] 'takeoff 20' → 'takeoff to 20 meters'
[PASS] 'takeoff drone 20' → 'takeoff to 20 meters'
...
============================================================
Results: 11 passed, 0 failed
============================================================
```

### 3. Interactive Demo Mode

```bash
docker run -it --rm ap_offline_chat_tool
```

**What to expect:**
1. Container starts
2. Ollama service initializes (~10 seconds)
3. Model downloads (first run only, ~1-2 minutes)
4. Demo interface appears

**Try these commands:**
- `arm the drone`
- `takeoff 20`
- `check battery`
- `/quit` to exit

### 4. Verify Python Imports

```bash
docker run --rm ap_offline_chat_tool python3 -c "import pymavlink, rich, ollama; print('All imports successful')"
```

**Expected Output:**
```
All imports successful
```

### 5. Check Ollama Installation

```bash
docker run --rm ap_offline_chat_tool ollama --version
```

**Expected Output:**
```
ollama version <version_number>
```

## Advanced Tests

### Run Specific Test File

```bash
# Test arm function
docker run --rm ap_offline_chat_tool python3 tests/test_arm.py

# Test movement functions
docker run --rm ap_offline_chat_tool python3 tests/test_movement.py
```

### Interactive Shell

```bash
# Get a bash shell inside container
docker run -it --rm ap_offline_chat_tool bash

# Inside container, you can:
python3 tests/test_suite.py
python3 examples/demo.py
ollama list
exit
```

### With Persistent Model Storage

```bash
# Create volume for Ollama models
docker volume create ollama-models

# Run with persistent storage
docker run -it --rm \
  -v ollama-models:/home/ardupilot/.ollama \
  ap_offline_chat_tool

# Model only downloads once!
```

## Troubleshooting

### Container Won't Start

```bash
# Check Docker is running
docker ps

# Check for errors
docker logs <container_id>

# Rebuild without cache
docker build --no-cache -t ap_offline_chat_tool .
```

### Tests Fail

```bash
# Check container logs
docker run --rm ap_offline_chat_tool python3 tests/test_suite.py 2>&1 | tee test_output.log

# Verify Python version
docker run --rm ap_offline_chat_tool python3 --version

# Check dependencies
docker run --rm ap_offline_chat_tool pip list
```

### Model Download Fails

```bash
# Check internet connection
ping ollama.com

# Try pulling model manually
docker run -it --rm ap_offline_chat_tool bash
# Inside container:
ollama serve &
sleep 5
ollama pull deepakpopli/ardupilot-stage1
```

## Performance Benchmarks

### Expected Timings

- **Build time** (first build): ~5-7 minutes
- **Build time** (cached): ~30 seconds
- **Model download** (first run): ~1-2 minutes (552MB)
- **Container startup**: ~10 seconds
- **Test suite**: ~5-10 seconds
- **Preprocessing tests**: ~2-3 seconds

### Resource Usage

- **Image size**: ~1.5 GB
- **Container RAM**: ~500 MB (idle), ~1 GB (running)
- **CPU**: Minimal (model inference is fast)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t ap_offline_chat_tool .
      
      - name: Run test suite
        run: docker run --rm ap_offline_chat_tool python3 tests/test_suite.py
      
      - name: Run preprocessing tests
        run: docker run --rm ap_offline_chat_tool python3 tests/test_preprocessing.py
```

## Quick Test Script

Save this as `test_docker.sh`:

```bash
#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t ap_offline_chat_tool .

echo "Running test suite..."
docker run --rm ap_offline_chat_tool python3 tests/test_suite.py

echo "Running preprocessing tests..."
docker run --rm ap_offline_chat_tool python3 tests/test_preprocessing.py

echo "All tests passed!"
```

Run with:
```bash
chmod +x test_docker.sh
./test_docker.sh
```

## Summary

**Minimum test commands:**
```bash
# Build
docker build -t ap_offline_chat_tool .

# Test
docker run --rm ap_offline_chat_tool python3 tests/test_suite.py

# Demo
docker run -it --rm ap_offline_chat_tool
```

If all three work, your Docker setup is correct!

---

For more Docker documentation, see [DOCKER.md](DOCKER.md)
