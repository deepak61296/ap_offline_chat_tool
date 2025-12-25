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
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "[2/4] Waiting for Ollama to be ready..."
sleep 5

# Check if model exists, if not pull/create it
echo "[3/4] Setting up ardupilot-stage1 model..."
if ollama list | grep -q "ardupilot-stage1"; then
    echo "Model already exists"
else
    echo "Creating model from Modelfile..."
    cd /app/models
    ollama create ardupilot-stage1 -f ardupilot-stage1.Modelfile
    
    # Alternative: Pull from Ollama library (if available)
    # ollama pull deepakpopli/ardupilot-stage1
fi

echo "[4/4] Setup complete!"
echo ""
echo "========================================="
echo "Ready to use ArduPilot AI Assistant!"
echo "========================================="
echo ""

# Execute the main command
exec "$@"
