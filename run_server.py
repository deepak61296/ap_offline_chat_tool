#!/usr/bin/env python3
"""
Entry point for ArduPilot AI Backend Server
Handles module imports correctly
"""

import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Now import and run the server
from backend.api_server import app
from backend.config import API_HOST, API_PORT, API_DEBUG, DEFAULT_MODEL

if __name__ == '__main__':
    print("=" * 70)
    print("ArduPilot AI Backend - HTTP API Server v2.2")
    print("=" * 70)
    print(f"Default Model: {DEFAULT_MODEL}")
    print(f"Modes: Agent (commands) | Ask (read-only) | Script (Lua generation)")
    print(f"Server running on: http://{API_HOST}:{API_PORT}")
    print("=" * 70)
    print("Endpoints:")
    print("  GET  /health  - Health check")
    print("  GET  /status  - Backend status")
    print("  GET  /models  - Available models")
    print("  POST /chat    - Send message (with mode)")
    print("=" * 70)
    print("Script Mode Features (V2 EXPANDED):")
    print("  - Template injection (21 proven patterns)")
    print("    * Basic monitoring (5 patterns)")
    print("    * Autonomous actions (2 patterns)")
    print("    * Arming checks (3 patterns)")
    print("    * Logging (SD card + dataflash)")
    print("    * Multi-sensor (AND/OR logic)")
    print("    * Safety (geofence, vibration, EKF)")
    print("    * Parameters & state machines")
    print("  - LLM generation (qwen2.5-coder:7b)")
    print("  - Post-processing (auto-fix common errors)")
    print("=" * 70)
    print("Press Ctrl+C to stop the server")
    print("=" * 70)

    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=API_DEBUG,
        threaded=True
    )
