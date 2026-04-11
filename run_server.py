#!/usr/bin/env python3
"""Entry point for the ArduPilot AI Backend."""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from backend.api_server import create_app
from backend.config import BACKEND_VERSION, parse_runtime_settings

try:
    from backend.mavlink_manager import PYMAVLINK_AVAILABLE
except ImportError:
    PYMAVLINK_AVAILABLE = False


def main(argv=None):
    settings = parse_runtime_settings(argv)
    app = create_app(settings)

    print("=" * 70)
    print(f"ArduPilot AI Backend - HTTP API Server v{BACKEND_VERSION}")
    print("=" * 70)
    print(f"Operation Mode: {settings.operation_mode}")
    print(f"Approval Mode:  {settings.approval_mode}")
    print(f"Default Model:  {settings.default_model}")
    print(f"Script Model:   {settings.script_model}")
    print(f"pymavlink:      {'Available' if PYMAVLINK_AVAILABLE else 'Not installed'}")
    print("=" * 70)
    print("Modes:")
    print("  Agent  - Execute commands (ARM, TAKEOFF, LAND, etc.)")
    print("  Ask    - Read-only telemetry queries")
    print("  Script - Lua script generation")
    print("=" * 70)
    print("Endpoints:")
    print("  GET  /health      - Health check")
    print("  GET  /status      - Backend status + models")
    print("  GET  /models      - Available Ollama models")
    print("  POST /chat        - AI chat (main endpoint)")
    print("  GET  /telemetry   - Current telemetry")
    print("  POST /connect     - Connect to vehicle")
    print("  POST /disconnect  - Disconnect from vehicle")
    print("  POST /command     - Execute command")
    print("=" * 70)
    print(f"Server: http://{settings.api_host}:{settings.api_port}")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.api_debug,
        threaded=True,
    )


if __name__ == "__main__":
    main()
