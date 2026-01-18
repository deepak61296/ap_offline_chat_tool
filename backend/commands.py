"""
Command extraction logic for ArduPilot AI Backend
Detects and parses drone commands from AI responses
"""

import re
from typing import Optional, Dict, Any
from backend.config import SUPPORTED_MODES, MOVEMENT_MAX_DISTANCE, TAKEOFF_MAX_ALTITUDE

def extract_command(ai_response: str) -> Optional[Dict[str, Any]]:
    """
    Extract drone command from AI response text
    ONLY extracts if AI explicitly says it's executing the command
    Returns: {"type": "COMMAND_TYPE", "params": {...}} or None
    """
    response_lower = ai_response.lower()
    
    # Split into lines and get first substantive line for basic command checking
    # This prevents multi-line responses from triggering wrong commands
    lines = [line.strip() for line in ai_response.split('\n') if line.strip()]
    first_line_lower = lines[0].lower() if lines else response_lower
    
    # Try each command type in order of specificity
    # Check first line only for basic commands to avoid conflicts
    
    # LAND command - check first line only
    if re.search(r'landing the drone', first_line_lower):
        return {"type": "LAND", "params": {}}
    
    # ARM command - check first line only
    if re.search(r'arming the drone now', first_line_lower) and not re.search(r'\bdisarm', first_line_lower):
        return {"type": "ARM", "params": {}}
    
    # DISARM command - check first line only
    if re.search(r'disarming the drone', first_line_lower):
        return {"type": "DISARM", "params": {}}
    
    # TAKEOFF command with altitude - check full response
    takeoff_match = re.search(r'taking off to (\d+)\s*(?:meters|m\b)', response_lower)
    if takeoff_match:
        altitude = int(takeoff_match.group(1))
        if altitude > TAKEOFF_MAX_ALTITUDE:
            return {"type": "ERROR", "params": {"message": f"Altitude {altitude}m exceeds maximum {TAKEOFF_MAX_ALTITUDE}m"}}
        return {"type": "TAKEOFF", "params": {"altitude": altitude}}
    
    # RTL (Return to Launch) command
    if re.search(r'returning to launch', response_lower):
        return {"type": "RTL", "params": {}}
    
    # REBOOT command
    if re.search(r'rebooting the flight controller', response_lower):
        return {"type": "REBOOT", "params": {}}

    
    # CHANGE_MODE command - detect mode changes
    mode_match = re.search(r'changing (?:mode|flight mode) to (\w+)', response_lower)
    if mode_match:
        mode = mode_match.group(1).upper()
        if mode not in SUPPORTED_MODES:
            return {"type": "ERROR", "params": {"message": f"Unsupported mode: {mode}"}}
        return {"type": "CHANGE_MODE", "params": {"mode": mode}}
    
    # Altitude change commands (must check before movement to avoid confusion)
    altitude_cmd = extract_altitude_command(ai_response)
    if altitude_cmd:
        return altitude_cmd
    
    # Movement commands
    movement_cmd = extract_movement_command(ai_response)
    if movement_cmd:
        return movement_cmd
    
    # GOTO command - detect coordinates
    goto_cmd = extract_goto_command(ai_response)
    if goto_cmd:
        return goto_cmd
    
    # Parameter commands
    param_cmd = extract_param_command(ai_response)
    if param_cmd:
        return param_cmd
    
    # No command detected
    return None


def extract_movement_command(ai_response: str) -> Optional[Dict[str, Any]]:
    """
    Extract directional movement commands
    Examples: "moving north 20 meters", "moving east 50m"
    """
    response_lower = ai_response.lower()
    
    # Pattern: "moving [direction] [distance] meters"
    directions = {
        'north': 0,
        'south': 180,
        'east': 90,
        'west': 270,
        'northeast': 45,
        'northwest': 315,
        'southeast': 135,
        'southwest': 225
    }
    
    for direction, bearing in directions.items():
        # More flexible pattern to match variations like:
        # "moving north 50 meters", "moving north for 50 meters", "moving 50 meters north"
        patterns = [
            rf'moving {direction}\s+(?:for\s+)?(\d+)\s*(?:meters|m\b)',  # "moving north for 50 meters"
            rf'moving\s+(\d+)\s*(?:meters|m\b)\s+{direction}',  # "moving 50 meters north"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_lower)
            if match:
                distance = int(match.group(1))
                if distance > MOVEMENT_MAX_DISTANCE:
                    return {"type": "ERROR", "params": {"message": f"Distance {distance}m exceeds maximum {MOVEMENT_MAX_DISTANCE}m"}}
                return {
                    "type": "MOVE_DIRECTION",
                    "params": {
                        "direction": direction.upper(),
                        "bearing": bearing,
                        "distance": distance
                    }
                }
    
    return None


def extract_altitude_command(ai_response: str) -> Optional[Dict[str, Any]]:
    """
    Extract altitude change commands
    Looks for "increasing altitude by X" or "decreasing altitude by X"
    """
    response_lower = ai_response.lower()
    
    # Look for "increasing altitude by X meters"
    increase_match = re.search(r'increasing altitude by (\d+)\s*(?:meters|m\b)', response_lower)
    if increase_match:
        altitude_change = int(increase_match.group(1))
        return {
            "type": "ALTITUDE_CHANGE",
            "params": {"altitude_change": altitude_change}
        }
    
    # Look for "decreasing altitude by X meters"
    decrease_match = re.search(r'decreasing altitude by (\d+)\s*(?:meters|m\b)', response_lower)
    if decrease_match:
        altitude_change = -int(decrease_match.group(1))
        return {
            "type": "ALTITUDE_CHANGE",
            "params": {"altitude_change": altitude_change}
        }
    
    return None


def extract_goto_command(ai_response: str) -> Optional[Dict[str, Any]]:
    """
    Extract GOTO location commands
    Supports multiple formats:
    - "flying to coordinates 37.7749, -122.4194"
    - "flying to 37.7749, -122.4194 at 100 meters"
    - "flying to home"
    """
    response_lower = ai_response.lower()
    
    # Check for "flying to home"
    if re.search(r'flying to home', response_lower):
        return {"type": "GOTO_HOME", "params": {}}
    
    # More flexible pattern for coordinates with optional altitude
    # Handles: "flying to coordinates 37.7749, -122.4194"
    #         "flying to coordinates: 37.7749, -122.4194 at 100 meters"
    #         "flying to coordinates: Latitude 40.7128, Longitude -74.0060"
    coord_patterns = [
        # Standard format: "flying to [coordinates] LAT, LON [at ALT meters]"
        r'flying to (?:coordinates:?\s*)?(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)(?:\s+at\s+(\d+)\s*(?:meters|m\b))?',
        # Verbose format: "Latitude X, Longitude Y"
        r'latitude\s+(-?\d+\.?\d*)\s*,?\s*longitude\s+(-?\d+\.?\d*)',
    ]
    
    for pattern in coord_patterns:
        match = re.search(pattern, response_lower)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            altitude = int(match.group(3)) if len(match.groups()) >= 3 and match.group(3) else None
            
            # Validate coordinates
            if not (-90 <= lat <= 90):
                return {"type": "ERROR", "params": {"message": f"Invalid latitude: {lat}"}}
            if not (-180 <= lon <= 180):
                return {"type": "ERROR", "params": {"message": f"Invalid longitude: {lon}"}}
            
            params = {"latitude": lat, "longitude": lon}
            if altitude:
                params["altitude"] = altitude
            
            return {"type": "GOTO", "params": params}
    
    return None


def extract_param_command(ai_response: str) -> Optional[Dict[str, Any]]:
    """
    Extract parameter management commands
    Examples:
    - "setting parameter WPNAV_SPEED to 500"
    - "getting parameter BATT_CAPACITY"
    """
    response_lower = ai_response.lower()
    
    # SET_PARAM: "setting parameter X to Y" - more flexible patterns
    set_patterns = [
        r'setting parameter\s+(\w+)\s+to\s+([-\d.]+)',  # "setting parameter X to Y"
        r'setting\s+(\w+)\s+to\s+([-\d.]+)',  # "setting X to Y"
    ]
    
    for pattern in set_patterns:
        set_match = re.search(pattern, response_lower)
        if set_match:
            param_name = set_match.group(1).upper()
            param_value = float(set_match.group(2))
            return {
                "type": "SET_PARAM",
                "params": {
                    "name": param_name,
                    "value": param_value
                }
            }
    
    # GET_PARAM: "getting parameter X" - more flexible patterns
    get_patterns = [
        r'getting parameter\s+(\w+)',  # "getting parameter X"
        r'getting\s+(\w+)',  # "getting X"
    ]
    
    for pattern in get_patterns:
        get_match = re.search(pattern, response_lower)
        if get_match:
            param_name = get_match.group(1).upper()
            return {
                "type": "GET_PARAM",
                "params": {"name": param_name}
            }
    
    return None


def validate_command(command: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate command parameters
    Returns: (is_valid, error_message)
    """
    if not command or "type" not in command:
        return False, "Invalid command structure"
    
    cmd_type = command["type"]
    params = command.get("params", {})
    
    # Validate based on command type
    if cmd_type == "TAKEOFF":
        alt = params.get("altitude", 0)
        if alt <= 0:
            return False, "Altitude must be positive"
        if alt > TAKEOFF_MAX_ALTITUDE:
            return False, f"Altitude exceeds maximum {TAKEOFF_MAX_ALTITUDE}m"
    
    elif cmd_type == "MOVE_DIRECTION":
        dist = params.get("distance", 0)
        if dist <= 0:
            return False, "Distance must be positive"
        if dist > MOVEMENT_MAX_DISTANCE:
            return False, f"Distance exceeds maximum {MOVEMENT_MAX_DISTANCE}m"
    
    elif cmd_type == "GOTO":
        lat = params.get("latitude")
        lon = params.get("longitude")
        if lat is None or lon is None:
            return False, "Missing latitude or longitude"
        if not (-90 <= lat <= 90):
            return False, f"Invalid latitude: {lat}"
        if not (-180 <= lon <= 180):
            return False, f"Invalid longitude: {lon}"
    
    elif cmd_type == "CHANGE_MODE":
        mode = params.get("mode", "").upper()
        if mode not in SUPPORTED_MODES:
            return False, f"Unsupported mode: {mode}"
    
    return True, None
