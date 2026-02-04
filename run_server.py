#!/usr/bin/env python3
"""
Entry point for ArduPilot AI Backend Server
Cross-platform: Windows and Linux compatible
Supports: Mission Planner, MAVProxy, QGroundControl, Standalone
"""

import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Now import and run the server
from backend.api_server import app
from backend.config import (
    API_HOST, API_PORT, API_DEBUG, DEFAULT_MODEL,
    BACKEND_VERSION, OPERATION_MODE, APPROVAL_MODE
)

# Check pymavlink availability
try:
    from backend.mavlink_manager import PYMAVLINK_AVAILABLE
except ImportError:
    PYMAVLINK_AVAILABLE = False

if __name__ == '__main__':
    print("=" * 70)
    print(f"ArduPilot AI Backend - HTTP API Server v{BACKEND_VERSION}")
    print("=" * 70)
    print(f"Operation Mode: {OPERATION_MODE}")
    print(f"Approval Mode:  {APPROVAL_MODE}")
    print(f"Default Model:  {DEFAULT_MODEL}")
    print(f"pymavlink:      {'Available' if PYMAVLINK_AVAILABLE else 'Not installed'}")
    print("=" * 70)
    print("Modes:")
    print("  Agent  - Execute commands (ARM, TAKEOFF, LAND, etc.)")
    print("  Ask    - Read-only telemetry queries")
    print("  Script - Lua script generation (31 templates)")
    print("=" * 70)
    print("Endpoints:")
    print("  GET  /health      - Health check")
    print("  GET  /status      - Backend status + models")
    print("  GET  /models      - Available Ollama models")
    print("  POST /chat        - AI chat (main endpoint)")
    print("  GET  /telemetry   - Current telemetry (standalone)")
    print("  POST /connect     - Connect to vehicle (standalone)")
    print("  POST /disconnect  - Disconnect from vehicle")
    print("  POST /command     - Execute command (standalone)")
    print("=" * 70)
    print("Supported GCS:")
    print("  - Mission Planner (integrated)")
    print("  - MAVProxy (--ai_backend_enable)")
    print("  - QGroundControl (integrated)")
    print("  - Standalone (direct MAVLink)")
    print("=" * 70)
    print(f"Server: http://{API_HOST}:{API_PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=API_DEBUG,
        threaded=True
    )
