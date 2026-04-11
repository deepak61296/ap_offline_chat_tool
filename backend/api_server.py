#!/usr/bin/env python3
"""
ArduPilot AI Backend — Flask API Server
"""

from flask import Flask, current_app, jsonify, request
from flask_cors import CORS
import logging

from backend.commands import extract_lua_script
from backend.config import (
    BACKEND_VERSION,
    COMMAND_RISK_LEVELS,
    DEFAULT_RUNTIME_SETTINGS,
    DEFAULT_CONNECTIONS,
    RuntimeSettings,
)
from backend.deterministic_parser import is_command_like, parse_user_commands
from backend.executor import execute as executor_execute
from backend.planner import plan as planner_plan
from backend.prompts import get_ask_prompt, get_script_prompt
from backend.telemetry_data import format_telemetry_for_prompt
from backend.template_injector_v2 import generate_from_template
from backend.lua_postprocessor import postprocess_lua_script

try:
    import ollama
except ImportError:
    class _MissingOllama:
        host = None

        def __getattr__(self, name):
            raise RuntimeError("ollama Python package is not installed")

    ollama = _MissingOllama()

try:
    from backend.mavlink_manager import PYMAVLINK_AVAILABLE, get_mavlink_manager
except ImportError:
    PYMAVLINK_AVAILABLE = False
    get_mavlink_manager = None

logging.basicConfig(
    level=getattr(logging, DEFAULT_RUNTIME_SETTINGS.log_level),
    format=DEFAULT_RUNTIME_SETTINGS.log_format,
)
logger = logging.getLogger(__name__)


def _set_ollama_host(settings: RuntimeSettings) -> None:
    if settings.ollama_host:
        ollama.host = settings.ollama_host


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


def _telemetry_health(telemetry):
    if not telemetry:
        return "missing"
    if telemetry.get("gps", {}).get("fix_type") in ("NO_FIX", "UNKNOWN", "", 0):
        return "degraded"
    if telemetry.get("status", {}).get("mode") in ("UNKNOWN", ""):
        return "degraded"
    return "healthy"


def create_app(settings: RuntimeSettings = DEFAULT_RUNTIME_SETTINGS) -> Flask:
    _set_ollama_host(settings)

    app = Flask(__name__)
    CORS(app)
    app.config["RUNTIME_SETTINGS"] = settings
    app.config["COMMAND_RISK_LEVELS"] = COMMAND_RISK_LEVELS

    mavlink_mgr = None
    if PYMAVLINK_AVAILABLE and get_mavlink_manager:
        mavlink_mgr = get_mavlink_manager()
        if settings.standalone_mode and settings.mavlink_connection:
            _connect_standalone_mavlink(mavlink_mgr, settings)
    app.config["MAVLINK_MANAGER"] = mavlink_mgr

    logger.info("ArduPilot AI Backend v%s started", BACKEND_VERSION)
    logger.info("Mode: %s | Approval: %s", settings.operation_mode, settings.approval_mode)

    register_routes(app)
    return app


def get_runtime_settings() -> RuntimeSettings:
    return current_app.config["RUNTIME_SETTINGS"]


def get_runtime_mavlink_manager():
    return current_app.config.get("MAVLINK_MANAGER")


def _connect_standalone_mavlink(mavlink_mgr, settings: RuntimeSettings) -> None:
    candidates = []
    for candidate in (
        settings.mavlink_connection,
        DEFAULT_CONNECTIONS["sitl"],
        DEFAULT_CONNECTIONS["sitl_udp"],
    ):
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        logger.info("Standalone: connecting to %s", candidate)
        if mavlink_mgr.connect(candidate, settings.mavlink_baud):
            logger.info("Standalone: MAVLink heartbeat received on %s", candidate)
            return
        logger.warning("Standalone: no heartbeat on %s", candidate)

    logger.error("Standalone: no MAVLink heartbeat on any configured connection")


def _transport_connected(settings: RuntimeSettings, mavlink_mgr, telemetry) -> bool:
    if settings.standalone_mode:
        return bool(mavlink_mgr and mavlink_mgr.connected)
    return is_telemetry_valid(telemetry)


def _effective_connection_string(settings: RuntimeSettings, mavlink_mgr) -> str:
    if mavlink_mgr:
        actual = getattr(mavlink_mgr, "connection_string", "")
        if actual:
            return actual
    return settings.mavlink_connection


def register_routes(app: Flask) -> None:
    @app.route("/health", methods=["GET"])
    def health_check():
        settings = get_runtime_settings()
        mavlink_mgr = get_runtime_mavlink_manager()
        mav_status = mavlink_mgr.state.value if mavlink_mgr else "not_available"
        return jsonify({
            "status": "healthy",
            "service": "ArduPilot AI Backend",
            "version": BACKEND_VERSION,
            "operation_mode": settings.operation_mode,
            "mavlink_status": mav_status,
        }), 200

    @app.route("/status", methods=["GET"])
    def get_status():
        settings = get_runtime_settings()
        mavlink_mgr = get_runtime_mavlink_manager()
        model_error = None
        try:
            models = ollama.list()
            try:
                available_models = [m.model for m in models.models]
            except AttributeError:
                available_models = [m.get("name", "") for m in models.get("models", [])]
        except Exception as e:
            available_models = []
            model_error = str(e)

        telemetry = None
        if mavlink_mgr and mavlink_mgr.connected:
            telemetry = mavlink_mgr.telemetry.to_dict()

        return jsonify({
            "status": "running",
            "version": BACKEND_VERSION,
            "operation_mode": settings.operation_mode,
            "default_model": settings.default_model,
            "script_model": settings.script_model,
            "available_models": available_models,
            "model_error": model_error,
            "supported_models": settings.supported_models,
            "modes": ["agent", "ask", "script"],
            "mavlink": {
                "available": PYMAVLINK_AVAILABLE,
                "connected": mavlink_mgr.connected if mavlink_mgr else False,
                "connection_string": _effective_connection_string(settings, mavlink_mgr),
                "configured_connection_string": settings.mavlink_connection,
                "state": _connection_state(mavlink_mgr),
                "telemetry_health": _telemetry_health(telemetry),
            },
            "runtime": settings.summary(),
            "architecture": "agentic_v3_standalone_first",
        }), 200

    @app.route("/models", methods=["GET"])
    def get_models():
        settings = get_runtime_settings()
        try:
            models = ollama.list()
            model_list = []
            try:
                for m in models.models:
                    model_list.append({
                        "name": m.model,
                        "size": getattr(m, "size", 0),
                        "modified": str(getattr(m, "modified_at", "")),
                    })
            except AttributeError:
                for m in models.get("models", []):
                    model_list.append({
                        "name": m.get("name", ""),
                        "size": m.get("size", 0),
                        "modified": m.get("modified_at", ""),
                    })
            return jsonify({
                "models": model_list,
                "default": settings.default_model,
                "script_model": settings.script_model,
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/connect", methods=["POST"])
    def connect_vehicle():
        settings = get_runtime_settings()
        if not PYMAVLINK_AVAILABLE or not get_mavlink_manager:
            return jsonify({"success": False, "error": "pymavlink not installed"}), 400

        mavlink_mgr = get_runtime_mavlink_manager()
        if mavlink_mgr is None:
            mavlink_mgr = get_mavlink_manager()
            current_app.config["MAVLINK_MANAGER"] = mavlink_mgr

        data = request.get_json() or {}
        conn_str = data.get("connection_string", settings.mavlink_connection)
        baud = data.get("baud", settings.mavlink_baud)

        if not conn_str:
            return jsonify({"success": False, "error": "No connection string"}), 400

        try:
            success = mavlink_mgr.connect(conn_str, baud)
            return jsonify({
                "success": success,
                "connected": mavlink_mgr.connected,
                "message": "Connected" if success else "Failed",
            }), 200 if success else 500
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/disconnect", methods=["POST"])
    def disconnect_vehicle():
        mavlink_mgr = get_runtime_mavlink_manager()
        if mavlink_mgr and mavlink_mgr.connected:
            mavlink_mgr.disconnect()
            return jsonify({"success": True}), 200
        return jsonify({"success": False, "message": "Not connected"}), 400

    @app.route("/telemetry", methods=["GET"])
    def get_telemetry():
        mavlink_mgr = get_runtime_mavlink_manager()
        if mavlink_mgr and mavlink_mgr.connected:
            telemetry = mavlink_mgr.telemetry.to_dict()
            return jsonify({
                "success": True,
                "connected": True,
                "telemetry": telemetry,
                "telemetry_health": _telemetry_health(telemetry),
            }), 200
        return jsonify({"success": True, "connected": False, "telemetry": None}), 200

    @app.route("/command", methods=["POST"])
    def execute_command():
        mavlink_mgr = get_runtime_mavlink_manager()
        if not mavlink_mgr or not mavlink_mgr.connected:
            return jsonify({"success": False, "error": "Not connected"}), 400

        data = request.get_json()
        if not data or "type" not in data:
            return jsonify({"success": False, "error": "Missing command type"}), 400

        command = {"type": data["type"], "params": data.get("params", {})}
        try:
            result = mavlink_mgr.execute_command(command)
            return jsonify({
                "success": result.success,
                "message": result.message,
                "data": result.data,
            }), 200 if result.success else 500
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/chat", methods=["POST"])
    def chat():
        try:
            settings = get_runtime_settings()
            mavlink_mgr = get_runtime_mavlink_manager()
            data = request.get_json()
            if not data or "message" not in data:
                return jsonify({"success": False, "error": "Missing message"}), 400

            user_message = data["message"].strip()
            if not user_message:
                return jsonify({"success": False, "error": "Empty message"}), 400

            mode = data.get("mode", "agent").lower()
            if mode not in ("agent", "ask", "script"):
                mode = "agent"

            default_model = settings.script_model if mode == "script" else settings.default_model
            model = data.get("model", default_model)
            telemetry = data.get("telemetry") or {}

            if settings.standalone_mode and not telemetry and mavlink_mgr and mavlink_mgr.connected:
                telemetry = mavlink_mgr.telemetry.to_dict()

            transport_connected = _transport_connected(settings, mavlink_mgr, telemetry)
            telemetry_valid = is_telemetry_valid(telemetry)
            connection_status = "CONNECTED to drone" if transport_connected else "NOT CONNECTED to drone"
            if telemetry_valid:
                telemetry_str = format_telemetry_for_prompt(telemetry)
                telemetry_section = f"CURRENT TELEMETRY:\n{telemetry_str}"
            elif transport_connected:
                telemetry_section = "TELEMETRY: MAVLink connected. Telemetry stream is still initializing."
            else:
                telemetry_section = "TELEMETRY: No drone connected."

            logger.info(
                "[%s] '%s' (transport_connected=%s telemetry_valid=%s)",
                mode.upper(),
                user_message,
                transport_connected,
                telemetry_valid,
            )

            ai_response = None
            command = None
            commands_array = None
            agent_meta = {}

            if mode == "script":
                ai_response, command = _handle_script_mode(
                    user_message, model, connection_status, telemetry_section, settings
                )
            elif mode == "ask":
                ai_response = _handle_ask_mode(
                    user_message, model, connection_status, telemetry_section, settings
                )
            else:
                agent_result = _handle_agent_mode(
                    user_message,
                    model,
                    telemetry,
                    connection_status,
                    telemetry_section,
                    settings,
                    mavlink_mgr,
                )
                ai_response = agent_result["response"]
                command = agent_result.get("command")
                commands_array = agent_result.get("commands")
                agent_meta = agent_result

            response_data = {
                "success": agent_meta.get("success", True),
                "response": ai_response,
                "command": command,
                "mode": mode,
                "model": model,
                "operation_mode": settings.operation_mode,
                "error": agent_meta.get("execution_error"),
            }
            response_data.update({
                "interaction_type": agent_meta.get("interaction_type", "conversation" if mode != "agent" else None),
                "parse_source": agent_meta.get("parse_source"),
                "execution_attempted": agent_meta.get("execution_attempted", False),
                "execution_success": agent_meta.get("execution_success", False),
                "execution_error": agent_meta.get("execution_error"),
                "connection_state": _connection_state(mavlink_mgr),
                "step_results": agent_meta.get("step_results", []),
            })
            if commands_array:
                response_data["commands"] = commands_array

            status_code = 200 if response_data["success"] else 400
            return jsonify(response_data), status_code

        except Exception as e:
            logger.error("Chat error: %s", str(e), exc_info=True)
            return jsonify({
                "success": False,
                "response": None,
                "command": None,
                "error": str(e),
            }), 500

    @app.route("/test", methods=["GET"])
    def test_endpoint():
        settings = get_runtime_settings()
        return jsonify({
            "message": "ArduPilot AI Backend is running!",
            "version": BACKEND_VERSION,
            "architecture": "agentic_v3_standalone_first",
            "pipeline": "Planner -> Executor",
            "operation_mode": settings.operation_mode,
        }), 200


def _handle_agent_mode(
    user_message,
    model,
    telemetry,
    connection_status,
    telemetry_section,
    settings,
    mavlink_mgr,
):
    command_like, commands = parse_user_commands(user_message)
    parse_source = "deterministic" if commands else "none"
    ai_text = _commands_to_text(commands) if commands else ""

    if not command_like:
        canned = _agent_conversation_response(user_message, connection_status)
        if canned:
            return {
                "success": True,
                "response": canned,
                "command": None,
                "commands": None,
                "interaction_type": "conversation",
                "parse_source": "deterministic",
                "execution_attempted": False,
                "execution_success": False,
                "execution_error": None,
                "step_results": [],
            }

    if not commands:
        ai_text, commands = planner_plan(
            user_message=user_message,
            model=model,
            telemetry=telemetry,
            connection_status=connection_status,
            telemetry_section=telemetry_section,
        )
        if commands:
            parse_source = "llm"

    if not commands and command_like:
        logger.warning("Agent: command-like prompt produced no structured commands: %s", user_message)
        return {
            "success": False,
            "response": "I did not get a valid structured command, so I did not execute anything.",
            "command": None,
            "commands": None,
            "interaction_type": "command",
            "parse_source": "none",
            "execution_attempted": False,
            "execution_success": False,
            "execution_error": "No structured command was produced",
            "step_results": [],
        }

    if not commands:
        logger.info("Planner: conversational response (no tool calls)")
        return {
            "success": True,
            "response": ai_text,
            "command": None,
            "commands": None,
            "interaction_type": "conversation",
            "parse_source": "none",
            "execution_attempted": False,
            "execution_success": False,
            "execution_error": None,
            "step_results": [],
        }

    result = executor_execute(
        commands=commands,
        telemetry=telemetry,
        ai_response=ai_text,
        model=model,
        user_message=user_message,
        connection_status=connection_status,
        telemetry_section=telemetry_section,
        standalone_mode=settings.standalone_mode,
        mavlink_manager=mavlink_mgr,
    )

    logger.info(
        "Executor result: %s (%s/%s tasks)",
        result.plan_summary,
        result.tasks_executed,
        result.tasks_total,
    )
    return {
        "success": result.execution_success if settings.standalone_mode else True,
        "response": result.ai_response,
        "command": result.command,
        "commands": result.commands,
        "interaction_type": "command",
        "parse_source": parse_source,
        "execution_attempted": result.execution_attempted,
        "execution_success": result.execution_success,
        "execution_error": result.execution_error,
        "step_results": result.step_results or [],
    }


def _commands_to_text(commands):
    if not commands:
        return ""
    parts = []
    for command in commands:
        cmd_type = command["type"]
        params = command.get("params", {})
        if cmd_type == "TAKEOFF":
            parts.append(f"Takeoff to {params.get('altitude')}m")
        elif cmd_type == "CHANGE_MODE":
            parts.append(f"Change mode to {params.get('mode')}")
        elif cmd_type == "MOVE_DIRECTION":
            parts.append(f"Move {params.get('direction')} {params.get('distance')}m")
        else:
            parts.append(cmd_type.replace("_", " ").title())
    return "Planned: " + " -> ".join(parts)


def _agent_conversation_response(user_message, connection_status):
    text = user_message.strip().lower()
    if text in {"hi", "hello", "hey"}:
        return (
            "Hi. I can control the drone when MAVLink is connected. "
            "Try commands like `change mode to guided`, `arm drone`, or `takeoff to 10m`."
        )
    if text in {"?", "help", "what can you do", "what can you do?"}:
        return (
            f"{connection_status}.\n\n"
            "Agent commands I can execute: change mode, arm/disarm, takeoff, land, RTL, move, set speed, "
            "set heading, and get/set parameters. If MAVLink is disconnected, execution is blocked."
        )
    return None


def _connection_state(mavlink_mgr):
    if not mavlink_mgr:
        return "unavailable"
    if getattr(mavlink_mgr, "connected", False):
        return "connected"
    state = getattr(getattr(mavlink_mgr, "state", None), "value", None)
    return state or "disconnected"


def _handle_ask_mode(user_message, model, connection_status, telemetry_section, settings):
    system_prompt = get_ask_prompt(connection_status, telemetry_section)
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        options={"num_ctx": settings.ollama_num_ctx, "num_gpu": settings.ollama_num_gpu},
    )
    return response["message"]["content"].strip()


def _handle_script_mode(user_message, model, connection_status, telemetry_section, settings):
    template_code, template_name = generate_from_template(user_message)

    if template_code:
        ai_response = (
            f"I'll create that script for you:\n\n```lua\n{template_code}\n```\n\n"
            f"This uses the proven {template_name} pattern."
        )
        command = {
            "type": "LUA_SCRIPT",
            "params": {
                "code": template_code,
                "description": user_message[:100],
                "source": "template",
                "template_used": template_name,
            },
        }
        return ai_response, command

    system_prompt = get_script_prompt(connection_status, telemetry_section)
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        options={
            "num_ctx": settings.ollama_num_ctx,
            "num_gpu": settings.ollama_num_gpu,
            "temperature": 0.05,
        },
    )

    ai_response = response["message"]["content"].strip()
    command = extract_lua_script(ai_response)

    if command and command.get("type") == "LUA_SCRIPT":
        original_code = command["params"]["code"]
        processed_code, fixes = postprocess_lua_script(original_code)
        if fixes:
            command["params"]["code"] = processed_code
            command["params"]["fixes"] = fixes
        command["params"]["source"] = "llm_postprocessed" if fixes else "llm"

    return ai_response, command


app = None


if __name__ == "__main__":
    settings = DEFAULT_RUNTIME_SETTINGS
    app = create_app(settings)
    print("=" * 60)
    print(f"  ArduPilot AI Backend v{BACKEND_VERSION}")
    print("  Architecture: Agentic Pipeline v3")
    print("  Pipeline: Planner -> Executor")
    print("=" * 60)
    print(f"  Model: {settings.default_model}")
    print(f"  Mode: {settings.operation_mode} | Approval: {settings.approval_mode}")
    print(f"  PyMAVLink: {'yes' if PYMAVLINK_AVAILABLE else 'no'}")
    print("=" * 60)
    print(f"  Server: http://{settings.api_host}:{settings.api_port}")
    print("=" * 60)

    app.run(host=settings.api_host, port=settings.api_port, debug=settings.api_debug, threaded=True)
