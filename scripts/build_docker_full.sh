#!/bin/bash
# Build and test the full Docker container with ArduPilot SITL

set -e

echo "========================================="
echo "Building Full ArduPilot AI Container"
echo "========================================="
echo ""

echo "This will:"
echo "  - Build a ~3-4 GB Docker image"
echo "  - Include ArduPilot SITL + MAVProxy"
echo "  - Include Ollama + AI Assistant"
echo "  - Take ~15-20 minutes on first build"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "[1/3] Building Docker image..."
docker build -f Dockerfile.full -t ardupilot-ai-full .

echo ""
echo "[2/3] Running tests..."
docker run --rm ardupilot-ai-full test

echo ""
echo "[3/3] Build complete!"
echo ""
echo "========================================="
echo "Available Commands"
echo "========================================="
echo ""
echo "Demo mode (no SITL):"
echo "  docker run -it --rm ardupilot-ai-full demo"
echo ""
echo "SITL mode (full simulation):"
echo "  docker run -it --rm --privileged --network host ardupilot-ai-full sitl"
echo ""
echo "Run tests:"
echo "  docker run --rm ardupilot-ai-full test"
echo ""
echo "Interactive shell:"
echo "  docker run -it --rm ardupilot-ai-full bash"
echo ""
echo "========================================="
echo "Ready to use!"
echo "========================================="
