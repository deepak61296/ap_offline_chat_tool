#!/bin/bash
# Docker entrypoint script
# Sets up Ollama and the model, then runs the application

set -e

echo "========================================="
echo "ArduPilot AI Assistant - Docker Setup"
echo "========================================="
echo ""

# Start Ollama service in background
echo "[1/4] Starting Ollama service..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "[2/4] Waiting for Ollama to be ready..."
for i in {1..30}; do
    if ollama list > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    sleep 1
done

# Check if model exists, if not pull it
echo "[3/4] Setting up ardupilot-stage1 model..."
if ollama list | grep -q "ardupilot-stage1"; then
    echo "Model already exists"
else
    echo "Pulling model from Ollama library..."
    ollama pull deepakpopli/ardupilot-stage1
    echo "Model downloaded successfully!"
fi

echo "[4/4] Setup complete!"
echo ""
echo "========================================="
echo "Ready to use ArduPilot AI Assistant!"
echo "========================================="
echo ""

# Execute the main command
exec "$@"
