"""
Task Executor — The Hands of the Agentic Drone Copilot.

Takes an ordered list of commands from the Planner and processes them
intelligently:
- Single commands → returned directly to QGC for execution
- Movement sequences → compiled into GPS waypoints and uploaded as Auto Mission
- CIRCLE → sets radius param via PyMAVLink then triggers mode change
- SEARCH_PARAM → fetches from param_db, triggers Planner re-prompt
- Mixed sequences (ARM + TAKEOFF + MOVE) → returns first immediate command,
  queues complex parts as background mission

This module is the ONLY place where special agentic flows live.
"""

import math
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

from backend.commands import validate_command

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular deps
_mavlink_manager = None
_param_db = None


def _get_mavlink_manager():
    """Lazy-load MAVLink manager."""
    global _mavlink_manager
    if _mavlink_manager is None:
        try:
            from backend.mavlink_manager import get_mavlink_manager
            _mavlink_manager = get_mavlink_manager
        except ImportError:
            _mavlink_manager = lambda: None
    return _mavlink_manager()


def _get_param_db():
    """Lazy-load parameter database."""
    global _param_db
    if _param_db is None:
        try:
            from backend.param_db import db
            _param_db = db
        except ImportError:
            _param_db = None
    return _param_db


# ─────────────────────────────────────────────────────
# Coordinate Math
# ─────────────────────────────────────────────────────

def _offset_coords(lat: float, lon: float, yaw: float, distance: float, direction: str) -> Tuple[float, float]:
    """
    Calculate new GPS coordinates given a starting position, heading,
    distance, and direction (cardinal or relative).
    """
    angle = yaw  # Default: FORWARD uses current heading

    DIRECTION_ANGLES = {
        'NORTH': 0, 'SOUTH': 180, 'EAST': 90, 'WEST': 270,
        'NORTHEAST': 45, 'NORTHWEST': 315, 'SOUTHEAST': 135, 'SOUTHWEST': 225,
    }

    if direction in DIRECTION_ANGLES:
        angle = DIRECTION_ANGLES[direction]
    elif direction == 'BACKWARD' or direction == 'BACK':
        angle = yaw + 180.0
    elif direction == 'RIGHT':
        angle = yaw + 90.0
    elif direction == 'LEFT':
        angle = yaw - 90.0
    # else FORWARD: angle stays as yaw

    lat_offset = distance * math.cos(math.radians(angle)) / 111320.0
    lon_offset = distance * math.sin(math.radians(angle)) / (111320.0 * math.cos(math.radians(lat)))

    return lat + lat_offset, lon + lon_offset


# ─────────────────────────────────────────────────────
# Command Classification
# ─────────────────────────────────────────────────────

# Commands that QGC can execute immediately
IMMEDIATE_COMMANDS = {'ARM', 'DISARM', 'TAKEOFF', 'LAND', 'RTL', 'CHANGE_MODE',
                      'GOTO', 'ALTITUDE_CHANGE', 'SET_SPEED', 'SET_YAW',
                      'GET_PARAM', 'SET_PARAM', 'REBOOT', 'MOVE_DIRECTION'}

# Commands that need special backend processing
SPECIAL_COMMANDS = {'CIRCLE', 'SEARCH_PARAM', 'MISSION_PLAN'}


def _preflight_check(cmd: Dict, telemetry: dict) -> Optional[str]:
    """
    Pure Python pre-flight validation using telemetry.
    Returns a warning message if there's an issue, or None if all good.
    Zero LLM cost — the intelligence is in Python code, not the model.
    """
    cmd_type = cmd.get('type', '')
    status = telemetry.get('status', {})
    gps = telemetry.get('gps', {})
    is_armed = status.get('armed', False)
    mode = status.get('mode', '')
    alt = gps.get('altitude', 0)

    if cmd_type == 'TAKEOFF' and not is_armed:
        return "Warning: Drone is not armed. Arming first."

    if cmd_type == 'DISARM' and not is_armed:
        return None  # Already disarmed, skip silently

    if cmd_type in ('MOVE_DIRECTION', 'GOTO') and alt < 1 and is_armed:
        return "Warning: Drone is on the ground. Takeoff first before moving."

    if cmd_type == 'CIRCLE' and alt < 1:
        return "Warning: Drone needs to be airborne for CIRCLE mode."

    if cmd_type == 'ARM' and is_armed:
        return None  # Already armed, no-op

    return None


def _auto_inject_prerequisites(commands: List[Dict], telemetry: dict) -> List[Dict]:
    """
    Smart prerequisite injection — if user says 'takeoff 20m' but drone
    isn't armed, automatically prepend ARM. Pure Python logic.
    """
    status = telemetry.get('status', {})
    is_armed = status.get('armed', False)

    if not commands:
        return commands

    first_type = commands[0].get('type', '')

    # If first command is TAKEOFF but not armed, prepend ARM
    if first_type == 'TAKEOFF' and not is_armed:
        has_arm = any(c.get('type') == 'ARM' for c in commands)
        if not has_arm:
            logger.info("Executor: Auto-injecting ARM before TAKEOFF")
            commands.insert(0, {"type": "ARM", "params": {}})

    return commands


@dataclass
class ExecutionResult:
    """Result of executing a command plan."""
    ai_response: str              # Text to show user in QGC
    command: Optional[Dict]       # Single command for QGC to execute (or None)
    plan_summary: str             # Human-readable summary of what was planned
    tasks_total: int              # Total tasks in the plan
    tasks_executed: int           # How many were processed this cycle


# ─────────────────────────────────────────────────────
# The Main Executor
# ─────────────────────────────────────────────────────

def execute(
    commands: List[Dict[str, Any]],
    telemetry: dict,
    ai_response: str,
    model: str = "",
    user_message: str = "",
    connection_status: str = "",
    telemetry_section: str = "",
) -> ExecutionResult:
    """
    TRUE Agentic Executor — processes ALL commands in a single request.

    Strategy:
    1. Execute prerequisite commands (ARM, TAKEOFF) directly via PyMAVLink
    2. Compile movements into mission waypoints → upload via PyMAVLink
    3. Handle CIRCLE (set param + mode change)
    4. Handle SEARCH_PARAM (RAG double-hop)
    5. Return the final meaningful action to QGC

    This means "arm, takeoff 20m, move west 40m, circle 20m" happens
    in ONE request — ARM and TAKEOFF execute on the backend, then
    the circle or mission command is returned to QGC.
    """
    if not commands:
        return ExecutionResult(
            ai_response=ai_response,
            command=None,
            plan_summary="No commands to execute",
            tasks_total=0,
            tasks_executed=0,
        )

    # Smart pre-processing (pure Python, zero LLM cost)
    commands = _auto_inject_prerequisites(commands, telemetry)

    # Classify commands while preserving order
    plan_steps = []  # [(category, cmd), ...]
    for cmd in commands:
        is_valid, error = validate_command(cmd)
        if not is_valid:
            logger.warning(f"Executor: Skipping invalid command {cmd.get('type')}: {error}")
            continue

        cmd_type = cmd['type']
        if cmd_type == 'SEARCH_PARAM':
            plan_steps.append(('search', cmd))
        elif cmd_type == 'CIRCLE':
            plan_steps.append(('circle', cmd))
        elif cmd_type == 'MOVE_DIRECTION':
            plan_steps.append(('move', cmd))
        else:
            plan_steps.append(('immediate', cmd))

    if not plan_steps:
        return ExecutionResult(
            ai_response=ai_response,
            command=None,
            plan_summary="No valid commands found",
            tasks_total=len(commands),
            tasks_executed=0,
        )

    # ─── Handle SEARCH_PARAM first (RAG double-hop) ───
    search_cmds = [s for cat, s in plan_steps if cat == 'search']
    if search_cmds:
        return _handle_search_param(
            search_cmds[0], ai_response, model, user_message,
            connection_status, telemetry_section
        )

    # ─── Agentic Execution Loop ───
    # Execute prerequisites via PyMAVLink, collect final action for QGC
    mgr = _get_mavlink_manager()
    executed_steps = []
    movements = [s for cat, s in plan_steps if cat == 'move']
    circles = [s for cat, s in plan_steps if cat == 'circle']
    immediates = [s for cat, s in plan_steps if cat == 'immediate']

    logger.info(f"Executor: {len(immediates)} immediate, {len(movements)} movements, {len(circles)} circles")

    # Step 1: Execute immediate prerequisites (ARM, TAKEOFF, etc.) via PyMAVLink
    final_qgc_command = None

    if mgr and mgr.connected and len(plan_steps) > 1:
        # Multi-step plan: execute prerequisites directly on the backend
        for cat, cmd in plan_steps:
            if cat != 'immediate':
                continue

            cmd_type = cmd['type']

            # These are safe to execute directly via PyMAVLink
            if cmd_type in ('ARM', 'TAKEOFF', 'CHANGE_MODE', 'SET_SPEED', 'SET_YAW'):
                logger.info(f"Executor: Direct-executing {cmd_type} via PyMAVLink")
                result = mgr.execute_command(cmd)
                executed_steps.append(f"{cmd_type}: {'OK' if result.success else result.message}")

                # Wait for ARM/TAKEOFF to complete
                if cmd_type == 'ARM' and result.success:
                    import time
                    time.sleep(1)  # Give the FC a moment to arm
                elif cmd_type == 'TAKEOFF' and result.success:
                    import time
                    time.sleep(3)  # Wait for initial climb
            else:
                # Non-prerequisite immediate (LAND, RTL, GET_PARAM, etc.)
                # Save as the final QGC command
                final_qgc_command = cmd
                executed_steps.append(f"{cmd_type}: queued for QGC")
    else:
        # No PyMAVLink or single command: return first immediate to QGC
        if immediates:
            final_qgc_command = immediates[0]
            executed_steps.append(f"{immediates[0]['type']}: sent to QGC")

    # Step 2: Handle movements
    if movements:
        if len(movements) >= 2:
            mission_result = _handle_mission_plan(movements, telemetry, ai_response)
            if mission_result:
                executed_steps.append(f"Mission: {len(movements)} waypoints uploaded")
                # Mission upload returns CHANGE_MODE: AUTO
                final_qgc_command = mission_result.command
        elif len(movements) == 1 and not final_qgc_command:
            # Single movement — send to QGC if nothing else is pending
            final_qgc_command = movements[0]
            executed_steps.append(f"Move: {movements[0]['params']['direction']} {movements[0]['params']['distance']}m")
        elif len(movements) == 1 and mgr and mgr.connected:
            # Single movement but we have other commands — execute directly
            move_cmd = movements[0]
            direction = move_cmd['params']['direction']
            distance = move_cmd['params']['distance']
            gps = telemetry.get('gps', {})
            yaw = telemetry.get('attitude', {}).get('yaw', 0)
            base_lat = gps.get('latitude', 0)
            base_lon = gps.get('longitude', 0)
            base_alt = gps.get('altitude', 20)

            if base_lat != 0 or base_lon != 0:
                new_lat, new_lon = _offset_coords(base_lat, base_lon, yaw, distance, direction)
                goto_cmd = {"type": "GOTO", "params": {
                    "latitude": new_lat, "longitude": new_lon, "altitude": base_alt
                }}
                result = mgr.execute_command(goto_cmd)
                executed_steps.append(f"Move {direction} {distance}m: {'OK' if result.success else result.message}")
                import time
                time.sleep(2)  # Let drone start moving

    # Step 3: Handle circles
    if circles:
        circle_result = _handle_circle(circles[0], ai_response)
        executed_steps.append(f"Circle: radius={circles[0]['params']['radius']}m")
        final_qgc_command = circle_result.command

    # Build summary
    total_tasks = len(plan_steps)
    tasks_done = len(executed_steps)
    summary = " → ".join(executed_steps) if executed_steps else "No tasks executed"

    # Build enhanced response
    if len(executed_steps) > 1:
        step_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(executed_steps))
        enhanced_response = f"{ai_response}\n\nPlan executed ({tasks_done}/{total_tasks} steps):\n{step_text}"
    else:
        enhanced_response = ai_response

    logger.info(f"Executor: {summary} ({tasks_done}/{total_tasks} tasks)")

    return ExecutionResult(
        ai_response=enhanced_response,
        command=final_qgc_command,
        plan_summary=summary,
        tasks_total=total_tasks,
        tasks_executed=tasks_done,
    )


# ─────────────────────────────────────────────────────
# Special Flow Handlers
# ─────────────────────────────────────────────────────

def _handle_mission_plan(
    movements: List[Dict], telemetry: dict, ai_response: str
) -> Optional[ExecutionResult]:
    """Compile multiple movements into a GPS waypoint mission and upload via PyMAVLink."""
    base_lat = telemetry.get('gps', {}).get('latitude', 0)
    base_lon = telemetry.get('gps', {}).get('longitude', 0)
    base_alt = telemetry.get('gps', {}).get('altitude', 20)
    base_yaw = telemetry.get('attitude', {}).get('yaw', 0)

    if base_lat == 0 and base_lon == 0:
        logger.warning("Executor: Cannot build mission — no GPS position available")
        return ExecutionResult(
            ai_response=ai_response + "\n\nCannot execute mission: No GPS position available.",
            command=None,
            plan_summary="Mission failed: no GPS",
            tasks_total=len(movements),
            tasks_executed=0,
        )

    # Calculate waypoints
    waypoints = []
    curr_lat, curr_lon = base_lat, base_lon

    plan_parts = []
    for move in movements:
        direction = move['params']['direction']
        distance = move['params']['distance']
        curr_lat, curr_lon = _offset_coords(curr_lat, curr_lon, base_yaw, distance, direction)
        waypoints.append({"lat": curr_lat, "lon": curr_lon, "alt": base_alt})
        plan_parts.append(f"{direction.lower()} {distance}m")

    # Upload via PyMAVLink
    mgr = _get_mavlink_manager()
    if mgr:
        if not mgr.connected:
            logger.info("Executor: Connecting to ArduPilot via UDP for mission upload...")
            mgr.connect("udp:127.0.0.1:14551")

        logger.info(f"Executor: Uploading {len(waypoints)} waypoints...")
        result = mgr.upload_mission(waypoints)
        logger.info(f"Executor: Upload result: {result.message}")

        mission_text = " → ".join(plan_parts)
        return ExecutionResult(
            ai_response=ai_response + f"\n\nMission uploaded: {mission_text}. Switching to AUTO.",
            command={"type": "CHANGE_MODE", "params": {"mode": "AUTO"}},
            plan_summary=f"Mission: {mission_text}",
            tasks_total=len(movements),
            tasks_executed=len(movements),
        )
    else:
        logger.warning("Executor: PyMAVLink not available for mission upload")
        # Fallback: return first movement only
        return ExecutionResult(
            ai_response=ai_response,
            command=movements[0],
            plan_summary="Single movement (PyMAVLink unavailable)",
            tasks_total=len(movements),
            tasks_executed=1,
        )


def _handle_circle(circle_cmd: Dict, ai_response: str) -> ExecutionResult:
    """Set CIRCLE_RADIUS parameter and trigger CIRCLE flight mode."""
    radius = circle_cmd['params']['radius']

    mgr = _get_mavlink_manager()
    if mgr:
        if not mgr.connected:
            mgr.connect("udp:127.0.0.1:14551")
        # ArduPilot stores circle radius in centimeters
        mgr.set_parameter("CIRCLE_RADIUS", radius * 100.0)
        logger.info(f"Executor: Set CIRCLE_RADIUS={radius * 100.0}cm")

    return ExecutionResult(
        ai_response=ai_response + f"\n\nSet circle radius to {radius}m. Engaging CIRCLE mode.",
        command={"type": "CHANGE_MODE", "params": {"mode": "CIRCLE"}},
        plan_summary=f"Circle radius={radius}m",
        tasks_total=1,
        tasks_executed=1,
    )


def _handle_search_param(
    search_cmd: Dict,
    ai_response: str,
    model: str,
    user_message: str,
    connection_status: str,
    telemetry_section: str,
) -> ExecutionResult:
    """RAG double-hop: search param_db, inject results, re-prompt the Planner."""
    query = search_cmd['params']['query']
    logger.info(f"Executor: RAG search for '{query}'")

    db = _get_param_db()
    if not db:
        return ExecutionResult(
            ai_response="Parameter database is not available.",
            command=None,
            plan_summary="RAG failed: no database",
            tasks_total=1,
            tasks_executed=0,
        )

    results = db.search(query, top_k=5)

    if results:
        context = "SYSTEM: Here are the ArduPilot parameters matching your query:\n"
        for i, r in enumerate(results):
            context += f"{i+1}. {r['name']} — {r['description'][:120]}\n"
        context += "\nNow use the correct parameter name in a get_param or set_param tool call."
    else:
        context = f"SYSTEM: No parameters found matching '{query}'. Please inform the user."

    # Re-prompt the Planner with the injected context
    from backend.planner import replan_with_context
    new_text, new_commands = replan_with_context(
        user_message=user_message,
        previous_response=ai_response,
        injected_context=context,
        model=model,
        connection_status=connection_status,
        telemetry_section=telemetry_section,
    )

    # Process the re-planned commands (should be GET_PARAM or SET_PARAM now)
    if new_commands:
        cmd = new_commands[0]
        is_valid, error = validate_command(cmd)
        if is_valid:
            return ExecutionResult(
                ai_response=new_text,
                command=cmd,
                plan_summary=f"RAG resolved: {cmd['type']} {cmd.get('params', {}).get('name', '')}",
                tasks_total=1,
                tasks_executed=1,
            )

    # RAG didn't resolve to a command — return the text explanation
    return ExecutionResult(
        ai_response=new_text,
        command=None,
        plan_summary="RAG: informational response",
        tasks_total=1,
        tasks_executed=1,
    )
