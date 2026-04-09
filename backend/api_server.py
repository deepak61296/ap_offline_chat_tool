#!/usr/bin/env python3
"""
ArduPilot AI Backend — Flask API Server v3.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Clean architecture:
  /chat → Planner (LLM) → Executor (agentic logic) → QGC response

Modules:
  planner.py    — LLM task decomposition (the brain)
  executor.py   — Agentic execution engine (the hands)
  tools.py      — Tool definitions + JSON extraction
  commands.py   — Legacy regex fallback
  mavlink_manager.py — Direct MAVLink vehicle comms
  param_db.py   — ArduPilot parameter RAG database
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import logging
import time

from backend.config import (
    API_HOST, API_PORT, API_DEBUG,
    DEFAULT_MODEL, SCRIPT_MODEL, LOG_LEVEL, LOG_FORMAT,
    STANDALONE_MODE, MAVLINK_CONNECTION, MAVLINK_BAUD,
    OPERATION_MODE, BACKEND_VERSION, COMMAND_RISK_LEVELS, APPROVAL_MODE,
    OLLAMA_NUM_CTX, OLLAMA_NUM_GPU
)
from backend.prompts import get_ask_prompt, get_script_prompt
from backend.commands import extract_command, validate_command, extract_lua_script
from backend.telemetry_data import format_telemetry_for_prompt
from backend.template_injector_v2 import generate_from_template
from backend.lua_postprocessor import postprocess_lua_script

# Agentic pipeline
from backend.planner import plan as planner_plan
from backend.executor import execute as executor_execute

# MAVLink manager (optional)
try:
    from backend.mavlink_manager import get_mavlink_manager, PYMAVLINK_AVAILABLE
except ImportError:
    PYMAVLINK_AVAILABLE = False
    get_mavlink_manager = None

# ─── Logging ───
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# ─── Flask App ───
app = Flask(__name__)
CORS(app)

# ─── Standalone MAVLink ───
mavlink_mgr = None
if STANDALONE_MODE and PYMAVLINK_AVAILABLE and get_mavlink_manager:
    mavlink_mgr = get_mavlink_manager()
    if MAVLINK_CONNECTION:
        logger.info(f"Standalone: connecting to {MAVLINK_CONNECTION}")
        mavlink_mgr.connect(MAVLINK_CONNECTION, MAVLINK_BAUD)

logger.info(f"ArduPilot AI Backend v{BACKEND_VERSION} started")
logger.info(f"Mode: {OPERATION_MODE} | Approval: {APPROVAL_MODE}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_telemetry_valid(telemetry):
    """Check if telemetry data indicates a real drone connection."""
    if not telemetry:
        return False
    if telemetry.get("battery", {}).get("voltage", 0) > 0:
        return True
    if telemetry.get("gps", {}).get("satellites", 0) > 0:
        return True
    mode = telemetry.get("status", {}).get("mode", "")
    if mode and mode not in ("UNKNOWN", ""):
        return True
    return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/health', methods=['GET'])
def health_check():
    mav_status = mavlink_mgr.state.value if mavlink_mgr else "not_available"
    return jsonify({
        'status': 'healthy',
        'service': 'ArduPilot AI Backend',
        'version': BACKEND_VERSION,
        'operation_mode': OPERATION_MODE,
        'mavlink_status': mav_status,
    }), 200


@app.route('/status', methods=['GET'])
def get_status():
    try:
        models = ollama.list()
        try:
            available_models = [m.model for m in models.models]
        except AttributeError:
            available_models = [m.get('name', '') for m in models.get('models', [])]

        mavlink_info = {
            'available': PYMAVLINK_AVAILABLE,
            'connected': mavlink_mgr.connected if mavlink_mgr else False,
        }

        return jsonify({
            'status': 'running',
            'version': BACKEND_VERSION,
            'operation_mode': OPERATION_MODE,
            'default_model': DEFAULT_MODEL,
            'available_models': available_models,
            'modes': ['agent', 'ask', 'script'],
            'mavlink': mavlink_info,
            'architecture': 'agentic_v3',
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/models', methods=['GET'])
def get_models():
    try:
        models = ollama.list()
        model_list = []
        try:
            for m in models.models:
                model_list.append({
                    'name': m.model,
                    'size': getattr(m, 'size', 0),
                    'modified': str(getattr(m, 'modified_at', ''))
                })
        except AttributeError:
            for m in models.get('models', []):
                model_list.append({
                    'name': m.get('name', ''),
                    'size': m.get('size', 0),
                    'modified': m.get('modified_at', '')
                })
        return jsonify({'models': model_list, 'default': DEFAULT_MODEL}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Standalone Endpoints ───

@app.route('/connect', methods=['POST'])
def connect_vehicle():
    if not PYMAVLINK_AVAILABLE:
        return jsonify({'success': False, 'error': 'pymavlink not installed'}), 400

    global mavlink_mgr
    if mavlink_mgr is None:
        mavlink_mgr = get_mavlink_manager()

    data = request.get_json() or {}
    conn_str = data.get('connection_string', MAVLINK_CONNECTION)
    baud = data.get('baud', MAVLINK_BAUD)

    if not conn_str:
        return jsonify({'success': False, 'error': 'No connection string'}), 400

    try:
        success = mavlink_mgr.connect(conn_str, baud)
        return jsonify({
            'success': success,
            'connected': mavlink_mgr.connected,
            'message': 'Connected' if success else 'Failed'
        }), 200 if success else 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/disconnect', methods=['POST'])
def disconnect_vehicle():
    if mavlink_mgr and mavlink_mgr.connected:
        mavlink_mgr.disconnect()
        return jsonify({'success': True}), 200
    return jsonify({'success': False, 'message': 'Not connected'}), 400


@app.route('/telemetry', methods=['GET'])
def get_telemetry():
    if mavlink_mgr and mavlink_mgr.connected:
        return jsonify({
            'success': True, 'connected': True,
            'telemetry': mavlink_mgr.telemetry.to_dict(),
        }), 200
    return jsonify({'success': True, 'connected': False, 'telemetry': None}), 200


@app.route('/command', methods=['POST'])
def execute_command():
    if not mavlink_mgr or not mavlink_mgr.connected:
        return jsonify({'success': False, 'error': 'Not connected'}), 400

    data = request.get_json()
    if not data or 'type' not in data:
        return jsonify({'success': False, 'error': 'Missing command type'}), 400

    command = {'type': data['type'], 'params': data.get('params', {})}
    try:
        result = mavlink_mgr.execute_command(command)
        return jsonify({
            'success': result.success, 'message': result.message,
            'data': result.data,
        }), 200 if result.success else 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THE CORE: /chat endpoint
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/chat', methods=['POST'])
def chat():
    """
    Process chat message using the Agentic Pipeline.
    
    Flow:
    1. Parse request, build telemetry context
    2. Route by mode:
       - script → template_injector or LLM Lua generation
       - ask    → simple LLM Q&A
       - agent  → Planner (decompose) → Executor (resolve) → QGC command
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'Missing message'}), 400

        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'success': False, 'error': 'Empty message'}), 400

        mode = data.get('mode', 'agent').lower()
        if mode not in ('agent', 'ask', 'script'):
            mode = 'agent'

        default_model = SCRIPT_MODEL if mode == 'script' else DEFAULT_MODEL
        model = data.get('model', default_model)
        telemetry = data.get('telemetry', {})

        # Build telemetry context
        is_connected = is_telemetry_valid(telemetry)
        connection_status = "CONNECTED to drone" if is_connected else "NOT CONNECTED to drone"
        telemetry_str = format_telemetry_for_prompt(telemetry) if is_connected else ""
        telemetry_section = f"CURRENT TELEMETRY:\n{telemetry_str}" if is_connected else "TELEMETRY: No drone connected."

        logger.info(f"[{mode.upper()}] '{user_message}' (connected={is_connected})")

        ai_response = None
        command = None
        commands_array = None

        # ─── SCRIPT MODE ───
        if mode == 'script':
            ai_response, command = _handle_script_mode(user_message, model, connection_status, telemetry_section)

        # ─── ASK MODE ───
        elif mode == 'ask':
            ai_response = _handle_ask_mode(user_message, model, connection_status, telemetry_section)

        # ─── AGENT MODE (The Agentic Pipeline) ───
        elif mode == 'agent':
            ai_response, command, commands_array = _handle_agent_mode(
                user_message, model, telemetry,
                connection_status, telemetry_section
            )

        response_data = {
            'success': True,
            'response': ai_response,
            'command': command,
            'mode': mode,
            'model': model,
            'error': None
        }
        # Include commands array for multi-step plans
        if commands_array:
            response_data['commands'] = commands_array

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False, 'response': None,
            'command': None, 'error': str(e)
        }), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Mode Handlers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _handle_agent_mode(user_message, model, telemetry, connection_status, telemetry_section):
    """
    The Agentic Pipeline:
    1. Planner decomposes the prompt into tool calls
    2. Executor processes them (mission upload, circle, RAG, etc.)
    3. Return the first executable command to QGC
    """
    # Step 1: Plan
    ai_text, commands = planner_plan(
        user_message=user_message,
        model=model,
        telemetry=telemetry,
        connection_status=connection_status,
        telemetry_section=telemetry_section,
    )

    if not commands:
        # No tool calls → conversational response (greeting, question, etc.)
        # Do NOT fall back to legacy regex — it causes false-positive commands
        logger.info("Planner: conversational response (no tool calls)")
        return ai_text, None, None

    # Step 2: Execute
    result = executor_execute(
        commands=commands,
        telemetry=telemetry,
        ai_response=ai_text,
        model=model,
        user_message=user_message,
        connection_status=connection_status,
        telemetry_section=telemetry_section,
    )

    logger.info(f"Executor result: {result.plan_summary} ({result.tasks_executed}/{result.tasks_total} tasks)")
    return result.ai_response, result.command, result.commands


def _handle_ask_mode(user_message, model, connection_status, telemetry_section):
    """Simple Q&A mode — no command execution."""
    system_prompt = get_ask_prompt(connection_status, telemetry_section)
    response = ollama.chat(
        model=model,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ],
        options={'num_ctx': OLLAMA_NUM_CTX, 'num_gpu': OLLAMA_NUM_GPU}
    )
    return response['message']['content'].strip()


def _handle_script_mode(user_message, model, connection_status, telemetry_section):
    """Lua script generation — template matching first, LLM fallback."""
    # Try template injection first
    template_code, template_name = generate_from_template(user_message)

    if template_code:
        logger.info(f"Template matched: {template_name}")
        ai_response = f"I'll create that script for you:\n\n```lua\n{template_code}\n```\n\nThis uses the proven {template_name} pattern."
        command = {
            "type": "LUA_SCRIPT",
            "params": {
                "code": template_code,
                "description": user_message[:100],
                "source": "template",
                "template_used": template_name
            }
        }
        return ai_response, command

    # LLM generation
    system_prompt = get_script_prompt(connection_status, telemetry_section)
    response = ollama.chat(
        model=model,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ],
        options={'num_ctx': OLLAMA_NUM_CTX, 'num_gpu': OLLAMA_NUM_GPU, 'temperature': 0.05}
    )

    ai_response = response['message']['content'].strip()
    command = extract_lua_script(ai_response)

    if command and command.get("type") == "LUA_SCRIPT":
        original_code = command["params"]["code"]
        processed_code, fixes = postprocess_lua_script(original_code)
        if fixes:
            command["params"]["code"] = processed_code
            command["params"]["fixes"] = fixes
        command["params"]["source"] = "llm_postprocessed" if fixes else "llm"

    return ai_response, command


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Endpoint
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        'message': 'ArduPilot AI Backend is running!',
        'version': BACKEND_VERSION,
        'architecture': 'agentic_v3',
        'pipeline': 'Planner → Executor → QGC',
    }), 200


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    print("=" * 60)
    print(f"  ArduPilot AI Backend v{BACKEND_VERSION}")
    print(f"  Architecture: Agentic Pipeline v3")
    print(f"  Pipeline: Planner → Executor → QGC")
    print("=" * 60)
    print(f"  Model: {DEFAULT_MODEL}")
    print(f"  Mode: {OPERATION_MODE} | Approval: {APPROVAL_MODE}")
    print(f"  PyMAVLink: {'✓' if PYMAVLINK_AVAILABLE else '✗'}")
    print("=" * 60)
    print(f"  Server: http://{API_HOST}:{API_PORT}")
    print("=" * 60)

    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG, threaded=True)