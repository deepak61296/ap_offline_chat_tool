#!/usr/bin/env python3
"""
ArduPilot AI Backend - HTTP API Server v2.1
Mission Planner Integration with Agent/Ask Modes

Refactored with modular structure:
- config.py: Configuration and safety limits
- prompts.py: AI prompts for Agent/Ask modes
- commands.py: Command extraction and validation
- telemetry_data.py: Telemetry formatting

Agent Mode: Execute commands (ARM, TAKEOFF, LAND, MOVE, PARAMS, etc.)
Ask Mode: Read-only telemetry queries
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import logging

# Import our modules
from backend.config import (
    API_HOST, API_PORT, API_DEBUG,
    DEFAULT_MODEL, LOG_LEVEL, LOG_FORMAT
)
from backend.prompts import get_agent_prompt, get_ask_prompt
from backend.commands import extract_command, validate_command
from backend.telemetry_data import format_telemetry_for_prompt

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

logger.info("AI Backend API Server v2.1 initialized")


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
    return jsonify({
        'status': 'healthy',
        'service': 'ArduPilot AI Backend',
        'version': '2.1.0',
        'features': ['agent_mode', 'ask_mode', 'telemetry', 'parameters', 'movement']
    }), 200


@app.route('/status', methods=['GET'])
def get_status():
    """Get backend status and model information"""
    try:
        models = ollama.list()
        available_models = [m.get('name', '') for m in models.get('models', [])]
        
        return jsonify({
            'status': 'running',
            'version': '2.1.0',
            'default_model': DEFAULT_MODEL,
            'available_models': available_models,
            'backend': 'Ollama',
            'modes': ['agent', 'ask'],
            'connection': 'ready',
            'features': {
                'commands': ['ARM', 'DISARM', 'TAKEOFF', 'LAND', 'RTL', 'CHANGE_MODE', 'GOTO', 'MOVE_DIRECTION'],
                'parameters': ['GET_PARAM', 'SET_PARAM'],
                'telemetry': True
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
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
        
        # Get mode (agent or ask)
        mode = data.get('mode', 'agent').lower()
        if mode not in ['agent', 'ask']:
            mode = 'agent'
        
        # Get model
        model = data.get('model', DEFAULT_MODEL)
        
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
        
        # Select prompt based on mode
        if mode == 'agent':
            system_prompt = get_agent_prompt(connection_status, telemetry_section)
        else:  # ask mode
            # Ask mode - no RAG, just use prompt
            system_prompt = get_ask_prompt(connection_status, telemetry_section, "")
        
        # Call Ollama API with CPU/GPU configuration
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
        
        # Extract command ONLY in agent mode
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
        'version': '2.1.0',
        'features': ['agent_mode', 'ask_mode', 'telemetry', 'multi_model', 'parameters', 'movement'],
        'endpoints': {
            'health': '/health',
            'status': '/status',
            'models': '/models',
            'chat': '/chat (POST)',
            'test': '/test'
        }
    }), 200


if __name__ == '__main__':
    print("=" * 70)
    print("ArduPilot AI Backend - HTTP API Server v2.1")
    print("=" * 70)
    print(f"Default Model: {DEFAULT_MODEL}")
    print(f"Modes: Agent (commands) | Ask (read-only)")
    print(f"Server running on: http://{API_HOST}:{API_PORT}")
    print("=" * 70)
    print("Endpoints:")
    print("  GET  /health  - Health check")
    print("  GET  /status  - Backend status")
    print("  GET  /models  - Available models")
    print("  POST /chat    - Send message (with mode)")
    print("=" * 70)
    print("Agent Mode Commands:")
    print("  - ARM, DISARM, TAKEOFF, LAND, RTL")
    print("  - CHANGE_MODE, GOTO, MOVE_DIRECTION")
    print("  - GET_PARAM, SET_PARAM")
    print("Ask Mode: Read-only telemetry queries")
    print("=" * 70)
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=API_DEBUG,
        threaded=True
    )