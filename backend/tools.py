"""
Agentic Tool-Calling Framework for ArduPilot AI Backend.

Instead of relying on fragile regex over free-text LLM output, this module
defines structured tools that the LLM outputs as JSON, and an agentic loop
that decomposes complex multi-step prompts into sequential tool calls.
"""

import json
import re
import math
import logging
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# Tool Definitions (what the AI can call)
# ─────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "arm",
        "description": "Arm the drone motors. Use before takeoff.",
        "parameters": {}
    },
    {
        "name": "disarm",
        "description": "Disarm the drone motors. Use after landing.",  
        "parameters": {}
    },
    {
        "name": "takeoff",
        "description": "Take off to a specified altitude in meters.",
        "parameters": {"altitude": "number (meters, required)"}
    },
    {
        "name": "land",
        "description": "Land the drone at current position.",
        "parameters": {}
    },
    {
        "name": "rtl",
        "description": "Return to launch / home position. Use for emergencies or bringing drone back.",
        "parameters": {}
    },
    {
        "name": "move",
        "description": "Move the drone in a direction by a distance. Supports cardinal (north/south/east/west) AND relative (forward/backward/left/right) directions.",
        "parameters": {
            "direction": "string (north|south|east|west|forward|backward|left|right, required)",
            "distance": "number (meters, required)"
        }
    },
    {
        "name": "circle",
        "description": "Make the drone orbit/circle at current position with a given radius.",
        "parameters": {"radius": "number (meters, required)"}
    },
    {
        "name": "goto",
        "description": "Fly to specific GPS coordinates.",
        "parameters": {
            "latitude": "number (required)",
            "longitude": "number (required)", 
            "altitude": "number (meters, optional)"
        }
    },
    {
        "name": "change_mode",
        "description": "Change the flight mode of the drone.",
        "parameters": {"mode": "string (GUIDED|AUTO|LOITER|STABILIZE|RTL|LAND|CIRCLE|ALT_HOLD, required)"}
    },
    {
        "name": "set_speed",
        "description": "Set the ground speed of the drone.",
        "parameters": {"speed": "number (m/s, required)"}
    },
    {
        "name": "set_altitude",
        "description": "Change altitude by a relative amount (positive=up, negative=down).",
        "parameters": {"change": "number (meters, positive=up negative=down, required)"}
    },
    {
        "name": "set_heading",
        "description": "Set the yaw/heading of the drone in degrees.",
        "parameters": {"heading": "number (0-360 degrees, required)"}
    },
    {
        "name": "get_param",
        "description": "Read a drone parameter value.",
        "parameters": {"name": "string (parameter name, required)"}
    },
    {
        "name": "set_param",
        "description": "Set a drone parameter to a value.",
        "parameters": {"name": "string (parameter name, required)", "value": "number (required)"}
    },
    {
        "name": "search_param",
        "description": "Search the parameter database for parameters related to a topic.",
        "parameters": {"query": "string (search term, required)"}
    },
    {
        "name": "reboot",
        "description": "Reboot the flight controller.",
        "parameters": {}
    }
]

def get_tools_description() -> str:
    """Format tool definitions for the system prompt."""
    lines = []
    for tool in TOOL_DEFINITIONS:
        params = tool["parameters"]
        if params:
            param_str = ", ".join([f'"{k}": {v}' for k, v in params.items()])
            lines.append(f'  - {tool["name"]}({param_str}): {tool["description"]}')
        else:
            lines.append(f'  - {tool["name"]}(): {tool["description"]}')
    return "\n".join(lines)


# ─────────────────────────────────────────────────────
# JSON Command Extraction (replaces fragile regex)
# ─────────────────────────────────────────────────────

def extract_tool_calls(ai_response: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extract structured tool calls from the AI response.
    
    The AI is instructed to output tool calls in a JSON block like:
    ```json
    [{"tool": "arm"}, {"tool": "takeoff", "params": {"altitude": 25}}]
    ```
    
    Returns: (clean_text_response, list_of_tool_calls)
    """
    tool_calls = []
    clean_text = ai_response
    
    # Strategy 1: Look for ```json code blocks
    json_block_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
    if json_block_match:
        try:
            parsed = json.loads(json_block_match.group(1))
            if isinstance(parsed, list):
                tool_calls = parsed
            elif isinstance(parsed, dict):
                tool_calls = [parsed]
            clean_text = ai_response[:json_block_match.start()].strip()
            if clean_text:
                return clean_text, tool_calls
            # If no text before json, try after
            clean_text = ai_response[json_block_match.end():].strip()
            return clean_text or "Executing commands.", tool_calls
        except json.JSONDecodeError:
            pass
    
    # Strategy 2: Look for raw JSON arrays [...] in the response
    json_array_match = re.search(r'\[[\s]*\{.*?\}[\s]*(?:,[\s]*\{.*?\}[\s]*)*\]', ai_response, re.DOTALL)
    if json_array_match:
        try:
            parsed = json.loads(json_array_match.group(0))
            if isinstance(parsed, list) and all(isinstance(x, dict) for x in parsed):
                tool_calls = parsed
                clean_text = ai_response[:json_array_match.start()].strip()
                if not clean_text:
                    clean_text = ai_response[json_array_match.end():].strip()
                return clean_text or "Executing commands.", tool_calls
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Look for single JSON object {"tool": ...}
    json_obj_match = re.search(r'\{[\s]*"tool"[\s]*:.*?\}', ai_response, re.DOTALL)
    if json_obj_match:
        try:
            parsed = json.loads(json_obj_match.group(0))
            if isinstance(parsed, dict) and "tool" in parsed:
                tool_calls = [parsed]
                clean_text = ai_response[:json_obj_match.start()].strip()
                if not clean_text:
                    clean_text = ai_response[json_obj_match.end():].strip()
                return clean_text or "Executing commands.", tool_calls
        except json.JSONDecodeError:
            pass
    
    return clean_text, tool_calls


def normalize_tool_call(tool_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert a tool call dict from the LLM into a standardized command dict
    that the existing QGC/MAVProxy infrastructure understands.
    """
    tool_name = tool_call.get("tool", "").lower().strip()
    params = tool_call.get("params", tool_call.get("parameters", {}))
    if not isinstance(params, dict):
        params = {}
    
    TOOL_MAP = {
        "arm":          lambda p: {"type": "ARM", "params": {}},
        "disarm":       lambda p: {"type": "DISARM", "params": {}},
        "takeoff":      lambda p: {"type": "TAKEOFF", "params": {"altitude": p.get("altitude", 10)}},
        "land":         lambda p: {"type": "LAND", "params": {}},
        "rtl":          lambda p: {"type": "RTL", "params": {}},
        "move":         lambda p: _normalize_move(p),
        "circle":       lambda p: {"type": "CIRCLE", "params": {"radius": p.get("radius", 10)}},
        "goto":         lambda p: {"type": "GOTO", "params": {
            "latitude": p.get("latitude", p.get("lat")),
            "longitude": p.get("longitude", p.get("lon")),
            "altitude": p.get("altitude", p.get("alt", 20))
        }},
        "change_mode":  lambda p: {"type": "CHANGE_MODE", "params": {"mode": p.get("mode", "GUIDED").upper()}},
        "set_speed":    lambda p: {"type": "SET_SPEED", "params": {"speed": p.get("speed", 5)}},
        "set_altitude": lambda p: {"type": "ALTITUDE_CHANGE", "params": {"change": p.get("change", 0)}},
        "set_heading":  lambda p: {"type": "SET_YAW", "params": {"heading": p.get("heading", 0)}},
        "get_param":    lambda p: {"type": "GET_PARAM", "params": {"name": p.get("name", "").upper()}},
        "set_param":    lambda p: {"type": "SET_PARAM", "params": {"name": p.get("name", "").upper(), "value": p.get("value", 0)}},
        "search_param": lambda p: {"type": "SEARCH_PARAM", "params": {"query": p.get("query", "")}},
        "reboot":       lambda p: {"type": "REBOOT", "params": {}},
    }
    
    handler = TOOL_MAP.get(tool_name)
    if handler:
        try:
            return handler(params)
        except Exception as e:
            logger.error(f"Error normalizing tool call '{tool_name}': {e}")
            return None
    
    logger.warning(f"Unknown tool: {tool_name}")
    return None


def _normalize_move(params: dict) -> dict:
    """Normalize a move command, handling direction aliases."""
    direction = str(params.get("direction", "forward")).upper()
    distance = params.get("distance", 10)
    
    # Normalize aliases
    if direction == "BACK":
        direction = "BACKWARD"
        
    return {
        "type": "MOVE_DIRECTION",
        "params": {
            "direction": direction,
            "distance": distance
        }
    }


# ─────────────────────────────────────────────────────
# Agentic Multi-Step Processor
# ─────────────────────────────────────────────────────

def build_mission_from_tools(tool_calls: List[Dict[str, Any]], telemetry: dict) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Given a list of tool calls, separate them into:
    - Immediate single commands (arm, takeoff, land, rtl, etc.)
    - Movement sequences that should be compiled into a MISSION_PLAN
    
    Returns: (immediate_commands, mission_plan_or_none)
    """
    immediate = []
    movements = []
    circle_cmd = None
    
    for tc in tool_calls:
        cmd = normalize_tool_call(tc)
        if not cmd:
            continue
            
        if cmd["type"] == "MOVE_DIRECTION":
            movements.append(cmd)
        elif cmd["type"] == "CIRCLE":
            circle_cmd = cmd
        else:
            immediate.append(cmd)
    
    # If we have multiple movements, create a MISSION_PLAN
    mission = None
    if len(movements) > 1:
        mission = {
            "type": "MISSION_PLAN",
            "sequence": movements
        }
    elif len(movements) == 1:
        immediate.append(movements[0])
    
    # Append circle after movements if present
    if circle_cmd:
        if mission:
            # Circle goes after the mission completes - handled separately
            immediate.append(circle_cmd)
        else:
            immediate.append(circle_cmd)
    
    return immediate, mission


def get_first_executable(tool_calls: List[Dict[str, Any]], telemetry: dict) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    From a list of tool calls, determine the single best command to execute NOW.
    Uses smart prioritization:
    - If there's a mission plan, upload it and return CHANGE_MODE AUTO
    - If there's a single command, return it
    - If there are multiple non-movement commands, return the first one
    
    Returns: (command_to_execute, human_readable_plan_summary)
    """
    immediate, mission = build_mission_from_tools(tool_calls, telemetry)
    
    plan_parts = []
    
    # If we have a mission plan, that takes priority
    if mission:
        for step in mission["sequence"]:
            d = step["params"]["direction"].lower()
            dist = step["params"]["distance"]
            plan_parts.append(f"{d} {dist}m")
        
        summary = "Mission plan: " + " → ".join(plan_parts)
        return mission, summary
    
    # Otherwise return immediate commands
    if immediate:
        # For circles, return the circle command directly
        first = immediate[0]
        if first["type"] == "CIRCLE":
            return first, f"Circle with radius {first['params']['radius']}m"
        return first, f"Executing: {first['type']}"
    
    return None, "No executable command found."
