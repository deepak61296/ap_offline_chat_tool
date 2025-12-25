#!/bin/bash
# Quick test script for Docker container with Ollama

echo "Testing Docker container with Ollama..."
echo ""

# Run container and wait for setup
echo "Starting container (this will take ~30 seconds for first-time setup)..."
echo ""

docker run -it --rm ardupilot-ai-assistant

# Note: The container will:
# 1. Start Ollama service
# 2. Create the ardupilot-stage1 model from Modelfile
# 3. Start the demo
#
# Then you can test commands like:
# - arm the drone
# - takeoff 20
# - check battery
# - /quit to exit
