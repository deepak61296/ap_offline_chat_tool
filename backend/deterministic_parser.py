"""Deterministic user-command parsing for safety-critical agent mode."""

import re
from typing import Dict, List, Tuple

from backend.commands import validate_command
from backend.config import SUPPORTED_MODES

COMMAND_WORDS = {
    "arm", "disarm", "takeoff", "take", "land", "rtl", "return", "launch",
    "mode", "guided", "loiter", "auto", "stabilize", "althold", "alt_hold",
    "move", "go", "fly", "north", "south", "east", "west", "forward",
    "backward", "left", "right", "speed", "heading", "yaw", "param",
    "parameter", "reboot", "abort", "danger", "home", "up", "down",
    "ascend", "descend", "climb", "drop",
}

CONVERSATIONAL_WORDS = {
    "hi", "hello", "hey", "thanks", "thank you", "what can you do",
}

NEGATION_PREFIXES = (
    "not ",
    "no ",
    "don't ",
    "dont ",
    "didn't ",
    "didnt ",
    "isn't ",
    "isnt ",
)


def is_command_like(text: str) -> bool:
    """Return True if the user text appears to request an action."""
    normalized = _normalize(text)
    if not normalized:
        return False
    if normalized in CONVERSATIONAL_WORDS:
        return False
    if normalized.startswith(NEGATION_PREFIXES):
        return False
    return any(re.search(rf"\b{re.escape(word)}\b", normalized) for word in COMMAND_WORDS)


def parse_user_commands(text: str) -> Tuple[bool, List[Dict]]:
    """
    Parse direct user input into command dictionaries.

    Returns (command_like, commands). If command_like is True and commands is empty,
    the caller should fail closed or ask for clarification instead of trusting prose.
    """
    normalized = _normalize(text)
    if not is_command_like(normalized):
        return False, []

    commands: List[Dict] = []
    for part in _split_steps(normalized):
        command = _parse_step(part)
        if command:
            valid, _ = validate_command(command)
            if valid:
                commands.append(command)

    return True, commands


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _split_steps(text: str) -> List[str]:
    parts = re.split(r"\b(?:then|after that|afterwards|followed by)\b|[,;]", text)
    expanded: List[str] = []
    for part in parts:
        # Split "arm and takeoff" but avoid breaking "change mode to guided".
        expanded.extend(re.split(r"\band\b(?=\s+(?:arm|disarm|takeoff|take off|land|rtl|return|move|go|fly|change|switch|set|reboot))", part))
    return [p.strip() for p in expanded if p.strip()]


def _parse_step(text: str):
    if re.search(r"\b(?:abort|danger|return to launch|rtl|come home|return home|bring (?:it|drone) back)\b", text):
        return {"type": "RTL", "params": {}}

    if re.search(r"\bdisarm\b", text):
        return {"type": "DISARM", "params": {}}

    if re.search(r"\barm\b", text):
        return {"type": "ARM", "params": {}}

    if re.search(r"\b(?:land|landing)\b", text):
        return {"type": "LAND", "params": {}}

    if re.search(r"\b(?:takeoff|take off)\b", text):
        altitude = _extract_number(text, default=10)
        return {"type": "TAKEOFF", "params": {"altitude": altitude}}

    mode = _parse_mode(text)
    if mode:
        return {"type": "CHANGE_MODE", "params": {"mode": mode}}

    movement = _parse_movement(text)
    if movement:
        return movement

    altitude = _parse_altitude_change(text)
    if altitude:
        return altitude

    speed = re.search(r"\b(?:set|change)?\s*speed\s*(?:to)?\s*(\d+(?:\.\d+)?)", text)
    if speed:
        return {"type": "SET_SPEED", "params": {"speed": float(speed.group(1))}}

    heading = re.search(r"\b(?:heading|yaw|face)\s*(?:to)?\s*(\d+(?:\.\d+)?)", text)
    if heading:
        return {"type": "SET_YAW", "params": {"heading": float(heading.group(1))}}

    set_param = re.search(r"\b(?:set|change|update)\s+(?:parameter\s+)?([A-Z0-9_]+)\s+to\s+(-?\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if set_param:
        return {"type": "SET_PARAM", "params": {"name": set_param.group(1).upper(), "value": float(set_param.group(2))}}

    get_param = re.search(r"\b(?:get|show|what is|check)\s+(?:parameter\s+)?([A-Z][A-Z0-9_]+)\b", text, re.IGNORECASE)
    if get_param:
        return {"type": "GET_PARAM", "params": {"name": get_param.group(1).upper()}}

    if re.search(r"\breboot\b", text):
        return {"type": "REBOOT", "params": {}}

    return None


def _parse_mode(text: str):
    match = re.search(r"\b(?:change|switch|set)\s+(?:flight\s+)?mode\s+(?:to\s+)?([a-z_]+)\b", text)
    if not match:
        match = re.search(r"\b(?:switch|change)\s+to\s+([a-z_]+)\b", text)
    if not match:
        return None

    mode = match.group(1).upper()
    aliases = {
        "ALTHOLD": "ALT_HOLD",
        "ALT": "ALT_HOLD",
        "ALTITUDE_HOLD": "ALT_HOLD",
        "POS_HOLD": "POSHOLD",
    }
    mode = aliases.get(mode, mode)
    return mode if mode in SUPPORTED_MODES else None


def _parse_movement(text: str):
    directions = "north|south|east|west|forward|backward|back|left|right"
    match = re.search(rf"\b(?:move|go|fly)\s+({directions})\s*(?:by|for)?\s*(\d+(?:\.\d+)?)?\s*(?:m|meter|meters)?\b", text)
    if not match:
        match = re.search(rf"\b(?:move|go|fly)\s+(\d+(?:\.\d+)?)\s*(?:m|meter|meters)?\s+({directions})\b", text)
        if match:
            distance = float(match.group(1))
            direction = match.group(2)
        else:
            return None
    else:
        direction = match.group(1)
        distance = float(match.group(2) or 10)

    if direction == "back":
        direction = "backward"
    return {"type": "MOVE_DIRECTION", "params": {"direction": direction.upper(), "distance": distance}}


def _parse_altitude_change(text: str):
    match = re.search(r"\b(?:go up|ascend|climb|increase altitude(?: by)?)\s*(\d+(?:\.\d+)?)", text)
    if match:
        return {"type": "ALTITUDE_CHANGE", "params": {"change": float(match.group(1))}}

    match = re.search(r"\b(?:go down|descend|drop|decrease altitude(?: by)?)\s*(\d+(?:\.\d+)?)", text)
    if match:
        return {"type": "ALTITUDE_CHANGE", "params": {"change": -float(match.group(1))}}

    return None


def _extract_number(text: str, default: float):
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else default
