#!/bin/bash
# Docker entrypoint script for full ArduPilot SITL + AI Assistant
# Supports multiple modes: demo, sitl, test

set -e

MODE="${1:-demo}"

echo "========================================="
echo "ArduPilot AI Assistant - Full Container"
echo "========================================="
echo ""

# Start Ollama service in background
echo "[1/5] Starting Ollama service..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "[2/5] Waiting for Ollama to be ready..."
for i in {1..30}; do
    if ollama list > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    sleep 1
done

# Check if model exists, if not pull it
echo "[3/5] Setting up ardupilot-stage1 model..."
if ollama list | grep -q "ardupilot-stage1"; then
    echo "Model already exists"
else
    echo "Pulling model from Ollama library (552MB, ~1-2 min)..."
    ollama pull deepakpopli/ardupilot-stage1
    echo "Model downloaded successfully!"
fi

echo "[4/5] Mode: $MODE"

case "$MODE" in
    "demo")
        echo "[5/5] Starting demo mode (no SITL)..."
        echo ""
        echo "========================================="
        echo "Ready! Running in DEMO mode"
        echo "========================================="
        echo ""
        cd /home/ardupilot/app
        exec python3 examples/demo.py
        ;;
    
    "sitl")
        echo "[5/5] Starting SITL + AI Assistant..."
        echo ""
        
        # Start SITL in background
        echo "Starting ArduCopter SITL..."
        cd /home/ardupilot/ardupilot/ArduCopter
        sim_vehicle.py -w --console --map > /tmp/sitl.log 2>&1 &
        SITL_PID=$!
        
        # Wait for SITL to be ready
        echo "Waiting for SITL to initialize (30 seconds)..."
        sleep 30
        
        echo ""
        echo "========================================="
        echo "Ready! SITL running, starting AI Assistant"
        echo "========================================="
        echo ""
        
        # Start AI Assistant
        cd /home/ardupilot/app
        exec python3 main.py
        ;;
    
    "test")
        echo "[5/5] Running tests..."
        echo ""
        cd /home/ardupilot/app
        
        echo "Running test suite..."
        python3 tests/test_suite.py
        
        echo ""
        echo "Running preprocessing tests..."
        python3 tests/test_preprocessing.py
        
        echo ""
        echo "========================================="
        echo "All tests complete!"
        echo "========================================="
        ;;
    
    "bash")
        echo "[5/5] Starting bash shell..."
        echo ""
        echo "========================================="
        echo "Interactive shell ready"
        echo "========================================="
        echo ""
        echo "Available commands:"
        echo "  - sim_vehicle.py (start SITL)"
        echo "  - python3 main.py (AI assistant with SITL)"
        echo "  - python3 examples/demo.py (demo mode)"
        echo "  - ollama list (check models)"
        echo ""
        exec /bin/bash
        ;;
    
    *)
        echo "Unknown mode: $MODE"
        echo "Available modes: demo, sitl, test, bash"
        exit 1
        ;;
esac
