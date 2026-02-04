#!/usr/bin/env python3
"""
ArduPilot AI Backend - HTTP API Server v2.4
Multi-GCS Support: Mission Planner, MAVProxy, QGroundControl, Standalone

Cross-platform: Windows and Linux compatible

Modes:
- Integrated: GCS sends telemetry, backend returns commands
- Standalone: Backend connects directly via MAVLink (pymavlink)

Refactored with modular structure:
- config.py: Configuration and safety limits
- prompts.py: AI prompts for Agent/Ask modes
- commands.py: Command extraction and validation
- telemetry_data.py: Telemetry formatting
- template_injector_v2.py: Ultimate template library (31 patterns!)
- lua_postprocessor.py: Post-processing for LLM-generated Lua
- mavlink_manager.py: Direct MAVLink connection (standalone mode)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import logging
import time

# Import our modules
from backend.config import (
    API_HOST, API_PORT, API_DEBUG,
    DEFAULT_MODEL, LOG_LEVEL, LOG_FORMAT,
    STANDALONE_MODE, MAVLINK_CONNECTION, MAVLINK_BAUD,
    OPERATION_MODE, BACKEND_VERSION, COMMAND_RISK_LEVELS, APPROVAL_MODE
)
from backend.prompts import get_agent_prompt, get_ask_prompt, get_script_prompt
from backend.commands import extract_command, validate_command, extract_lua_script
from backend.telemetry_data import format_telemetry_for_prompt
from backend.template_injector_v2 import generate_from_template
from backend.lua_postprocessor import postprocess_lua_script

# Import MAVLink manager (optional for standalone mode)
try:
    from backend.mavlink_manager import get_mavlink_manager, PYMAVLINK_AVAILABLE
except ImportError:
    PYMAVLINK_AVAILABLE = False
    get_mavlink_manager = None

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MAVLink manager instance (for standalone mode)
mavlink_mgr = None
if STANDALONE_MODE and PYMAVLINK_AVAILABLE and get_mavlink_manager:
    mavlink_mgr = get_mavlink_manager()
    if MAVLINK_CONNECTION:
        logger.info(f"Standalone mode: Connecting to {MAVLINK_CONNECTION}")
        mavlink_mgr.connect(MAVLINK_CONNECTION, MAVLINK_BAUD)

logger.info(f"AI Backend API Server v{BACKEND_VERSION} initialized")
logger.info(f"Operation mode: {OPERATION_MODE}")
logger.info(f"Approval mode: {APPROVAL_MODE}")


def is_telemetry_valid(telemetry):
    """Check if telemetry data indicates a real drone connection"""
    if not telemetry:
        return False
    
    # Check battery - if voltage is 0, no drone connected
    if "battery" in telemetry:
        voltage = telemetry["battery"].get("voltage", 0)
        if voltage > 0:
            return True
    
    # Check GPS - if satellites > 0, drone is connected
    if "gps" in telemetry:
        sats = telemetry["gps"].get("satellites", 0)
        if sats > 0:
            return True
    
    # Check status - if mode is not empty/default
    if "status" in telemetry:
        mode = telemetry["status"].get("mode", "")
        if mode and mode != "UNKNOWN" and mode != "":
            return True
    
    return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    mavlink_status = "not_available"
    if mavlink_mgr:
        mavlink_status = mavlink_mgr.state.value

    return jsonify({
        'status': 'healthy',
        'service': 'ArduPilot AI Backend',
        'version': BACKEND_VERSION,
        'operation_mode': OPERATION_MODE,
        'mavlink_status': mavlink_status,
        'features': ['agent_mode', 'ask_mode', 'script_mode', 'telemetry', 'parameters', 'movement', 'standalone'],
        'templates': 31,
        'template_system': 'v3_ultimate'
    }), 200


@app.route('/status', methods=['GET'])
def get_status():
    """Get backend status and model information"""
    try:
        models = ollama.list()
        available_models = [m.get('name', '') for m in models.get('models', [])]

        # Get MAVLink connection status
        mavlink_info = {
            'available': PYMAVLINK_AVAILABLE,
            'connected': False,
            'connection_string': ''
        }
        if mavlink_mgr:
            mavlink_info['connected'] = mavlink_mgr.connected
            mavlink_info['connection_string'] = mavlink_mgr._connection_string

        return jsonify({
            'status': 'running',
            'version': BACKEND_VERSION,
            'operation_mode': OPERATION_MODE,
            'approval_mode': APPROVAL_MODE,
            'default_model': DEFAULT_MODEL,
            'available_models': available_models,
            'backend': 'Ollama',
            'modes': ['agent', 'ask', 'script'],
            'mavlink': mavlink_info,
            'features': {
                'commands': ['ARM', 'DISARM', 'TAKEOFF', 'LAND', 'RTL', 'CHANGE_MODE', 'GOTO', 'MOVE_DIRECTION'],
                'parameters': ['GET_PARAM', 'SET_PARAM'],
                'telemetry': True,
                'standalone': PYMAVLINK_AVAILABLE
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ========================
# STANDALONE MODE ENDPOINTS
# ========================

@app.route('/connect', methods=['POST'])
def connect_vehicle():
    """
    Connect to vehicle via MAVLink (standalone mode)

    Request JSON:
    {
        "connection_string": "tcp:127.0.0.1:5760",
        "baud": 57600  (optional, for serial)
    }
    """
    if not PYMAVLINK_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'pymavlink not installed. Run: pip install pymavlink'
        }), 400

    global mavlink_mgr
    if mavlink_mgr is None:
        mavlink_mgr = get_mavlink_manager()

    data = request.get_json() or {}
    connection_string = data.get('connection_string', MAVLINK_CONNECTION)
    baud = data.get('baud', MAVLINK_BAUD)

    if not connection_string:
        return jsonify({
            'success': False,
            'error': 'No connection string provided'
        }), 400

    try:
        success = mavlink_mgr.connect(connection_string, baud)
        return jsonify({
            'success': success,
            'connected': mavlink_mgr.connected,
            'connection_string': connection_string,
            'message': 'Connected to vehicle' if success else 'Connection failed'
        }), 200 if success else 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/disconnect', methods=['POST'])
def disconnect_vehicle():
    """Disconnect from vehicle"""
    if mavlink_mgr and mavlink_mgr.connected:
        mavlink_mgr.disconnect()
        return jsonify({
            'success': True,
            'message': 'Disconnected from vehicle'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Not connected'
        }), 400


@app.route('/telemetry', methods=['GET'])
def get_telemetry():
    """
    Get current telemetry data

    Returns real-time telemetry in standalone mode,
    or empty data in integrated mode (GCS provides telemetry)
    """
    if mavlink_mgr and mavlink_mgr.connected:
        telemetry = mavlink_mgr.telemetry
        return jsonify({
            'success': True,
            'connected': True,
            'telemetry': telemetry.to_dict(),
            'timestamp': time.time()
        }), 200
    else:
        return jsonify({
            'success': True,
            'connected': False,
            'telemetry': None,
            'message': 'Not connected to vehicle (use /connect or GCS provides telemetry)'
        }), 200


@app.route('/command', methods=['POST'])
def execute_command():
    """
    Execute command directly (standalone mode)

    Request JSON:
    {
        "type": "ARM",
        "params": {}
    }
    """
    if not mavlink_mgr or not mavlink_mgr.connected:
        return jsonify({
            'success': False,
            'error': 'Not connected to vehicle'
        }), 400

    data = request.get_json()
    if not data or 'type' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing command type'
        }), 400

    command = {
        'type': data.get('type'),
        'params': data.get('params', {})
    }

    # Check command risk level
    risk_level = COMMAND_RISK_LEVELS.get(command['type'].upper(), 'high')

    try:
        result = mavlink_mgr.execute_command(command)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
            'risk_level': risk_level
        }), 200 if result.success else 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/models', methods=['GET'])
def get_models():
    """Get list of available models"""
    try:
        models = ollama.list()
        model_list = []
        
        for m in models.get('models', []):
            model_list.append({
                'name': m.get('name', ''),
                'size': m.get('size', 0),
                'modified': m.get('modified_at', '')
            })
        
        return jsonify({
            'models': model_list,
            'default': DEFAULT_MODEL
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/chat', methods=['POST'])
def chat():
    """
    Process chat message with mode support
    
    Request JSON:
    {
        "message": "user message",
        "mode": "agent" or "ask" (default: "agent"),
        "model": "model_name" (default: DEFAULT_MODEL),
        "telemetry": {...} (optional)
    }
    
    Response JSON:
    {
        "success": true/false,
        "response": "AI response text",
        "command": {"type": "...", "params": {...}} or null,
        "mode": "agent" or "ask",
        "model": "model_name",
        "error": "error message" or null
    }
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'response': None,
                'command': None,
                'error': 'Missing message in request'
            }), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                'success': False,
                'response': None,
                'command': None,
                'error': 'Empty message'
            }), 400
        
        # Get mode (agent, ask, or script)
        mode = data.get('mode', 'agent').lower()
        if mode not in ['agent', 'ask', 'script']:
            mode = 'agent'
        
        # Get model - use SCRIPT_MODEL for script mode, DEFAULT_MODEL for others
        from backend.config import SCRIPT_MODEL
        default_for_mode = SCRIPT_MODEL if mode == 'script' else DEFAULT_MODEL
        model = data.get('model', default_for_mode)
        
        # Get telemetry
        telemetry = data.get('telemetry', {})
        
        # Check if drone is actually connected
        is_connected = is_telemetry_valid(telemetry)
        
        if is_connected:
            connection_status = "CONNECTED to drone"
            telemetry_str = format_telemetry_for_prompt(telemetry)
            telemetry_section = f"CURRENT TELEMETRY:\\n{telemetry_str}"
        else:
            connection_status = "NOT CONNECTED to drone"
            telemetry_section = "TELEMETRY: No drone connected. All values are zero/default."
        
        logger.info(f"Processing message in {mode} mode: {user_message} (Connected: {is_connected})")
        
        # Initialize variables
        ai_response = None
        command = None
        template_code = None
        system_prompt = None

        # Select prompt based on mode
        if mode == 'agent':
            system_prompt = get_agent_prompt(connection_status, telemetry_section)
        elif mode == 'ask':
            # Ask mode - no RAG, just use prompt
            system_prompt = get_ask_prompt(connection_status, telemetry_section, "")
        else:  # script mode
            # Try template injection first (fast, guaranteed correct)
            template_code, template_used = generate_from_template(user_message)

            if template_code:
                # Template match! Use it directly (skip LLM!)
                logger.info(f"✓ Template matched: {template_used}")
                ai_response = f"I'll create that script for you:\n\n```lua\n{template_code}\n```\n\nThis script uses the proven {template_used} pattern from ArduPilot examples."
                command = {
                    "type": "LUA_SCRIPT",
                    "params": {
                        "code": template_code,
                        "description": user_message[:100],
                        "source": "template",
                        "template_used": template_used
                    }
                }
            else:
                # No template match - use LLM
                logger.info("No template match - using LLM generation")
                system_prompt = get_script_prompt(connection_status, telemetry_section)


        # Call Ollama API (only if not using template)
        if mode == 'script' and not template_code:
            # LLM generation for script mode
            from backend.config import OLLAMA_NUM_CTX, OLLAMA_NUM_GPU

            response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                options={
                    'num_ctx': OLLAMA_NUM_CTX,
                    'num_gpu': OLLAMA_NUM_GPU,
                    'temperature': 0.05,  # Low temperature for consistent code
                }
            )

            ai_response = response['message']['content'].strip()

            # Extract and post-process Lua script
            command = extract_lua_script(ai_response)
            if command and command.get("type") == "LUA_SCRIPT":
                # Apply post-processing to fix common mistakes
                original_code = command["params"]["code"]
                processed_code, fixes_applied = postprocess_lua_script(original_code)

                if fixes_applied:
                    logger.info(f"Post-processing applied: {', '.join(fixes_applied)}")
                    command["params"]["code"] = processed_code
                    command["params"]["source"] = "llm_postprocessed"
                    command["params"]["fixes"] = fixes_applied
                else:
                    command["params"]["source"] = "llm"

                logger.info(f"Lua script extracted: {command.get('params', {}).get('description', 'unknown')}")

        elif mode != 'script':
            # Agent/Ask mode - call LLM normally
            from backend.config import OLLAMA_NUM_CTX, OLLAMA_NUM_GPU

            response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                options={
                    'num_ctx': OLLAMA_NUM_CTX,
                    'num_gpu': OLLAMA_NUM_GPU
                }
            )

            ai_response = response['message']['content'].strip()

            # Extract command
            command = None
            if mode == 'agent':
                command = extract_command(ai_response)
                if command:
                    # Validate command
                    is_valid, error_msg = validate_command(command)
                    if not is_valid:
                        logger.warning(f"Invalid command: {error_msg}")
                        command = {"type": "ERROR", "params": {"message": error_msg}}
                    else:
                        logger.info(f"Command detected: {command['type']}")
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'command': command,
            'mode': mode,
            'model': model,
            'error': None
        }), 200
            
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        return jsonify({
            'success': False,
            'response': None,
            'command': None,
            'error': str(e)
        }), 500


@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API is working"""
    return jsonify({
        'message': 'API is working!',
        'version': BACKEND_VERSION,
        'operation_mode': OPERATION_MODE,
        'features': ['agent_mode', 'ask_mode', 'script_mode', 'telemetry', 'multi_model', 'parameters', 'movement', 'standalone'],
        'endpoints': {
            'health': 'GET /health',
            'status': 'GET /status',
            'models': 'GET /models',
            'chat': 'POST /chat',
            'telemetry': 'GET /telemetry',
            'connect': 'POST /connect',
            'disconnect': 'POST /disconnect',
            'command': 'POST /command',
            'test': 'GET /test'
        }
    }), 200


if __name__ == '__main__':
    print("=" * 70)
    print(f"ArduPilot AI Backend - HTTP API Server v{BACKEND_VERSION}")
    print("=" * 70)
    print(f"Operation Mode: {OPERATION_MODE}")
    print(f"Approval Mode: {APPROVAL_MODE}")
    print(f"Default Model: {DEFAULT_MODEL}")
    print(f"pymavlink: {'Available' if PYMAVLINK_AVAILABLE else 'Not installed'}")
    print("=" * 70)
    print("Modes:")
    print("  Agent  - Execute commands (ARM, TAKEOFF, LAND, etc.)")
    print("  Ask    - Read-only telemetry queries")
    print("  Script - Lua script generation (31 templates)")
    print("=" * 70)
    print("Endpoints:")
    print("  GET  /health      - Health check")
    print("  GET  /status      - Backend status")
    print("  GET  /models      - Available models")
    print("  POST /chat        - AI chat (main endpoint)")
    print("  GET  /telemetry   - Current telemetry (standalone)")
    print("  POST /connect     - Connect to vehicle (standalone)")
    print("  POST /disconnect  - Disconnect from vehicle")
    print("  POST /command     - Execute command (standalone)")
    print("=" * 70)
    print("Supported GCS:")
    print("  - Mission Planner (integrated mode)")
    print("  - MAVProxy (--ai_backend_enable)")
    print("  - QGroundControl (integrated mode)")
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