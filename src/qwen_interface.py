"""
Qwen 2.5 Communication Module
Handles communication with Ollama Qwen 2.5 model for drone control
Replaces FunctionGemma with superior natural language understanding
"""

import ollama
import re
import json
from typing import Dict, Any, Optional


class Qwen25Interface:
    """Interface for communicating with Qwen 2.5 via Ollama"""
    
    def __init__(self, model_name: str = "qwen2.5:3b"):
        """
        Initialize Qwen 2.5 interface
        
        Args:
            model_name: Name of the Ollama model to use (default: qwen2.5:3b)
        """
        self.model_name = model_name
        self.conversation_history = []
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with function definitions"""
        return """You are a drone command parser for ArduPilot. Convert natural language commands to JSON function calls.

Available functions:

BASIC CONTROL:
- arm() - Arm drone motors
- disarm() - Disarm drone motors
- takeoff(altitude) - Takeoff to altitude in meters
- land() - Land at current location
- rtl() - Return to launch
- change_mode(mode) - Change flight mode (GUIDED, LOITER, RTL, LAND, STABILIZE, AUTO)

COMPOSITE FUNCTIONS (NEW!):
- arm_and_takeoff(altitude) - Arm and takeoff in one command
- hover(duration) - Hold position for X seconds
- land_and_disarm() - Land and disarm automatically

ALTITUDE CONTROL:
- increase_altitude(meters) - Climb by X meters
- decrease_altitude(meters) - Descend by X meters

NAVIGATION:
- goto_location(lat, lon, alt) - Go to GPS coordinates
- move_north(meters) - Move north
- move_south(meters) - Move south
- move_east(meters) - Move east
- move_west(meters) - Move west
- set_yaw(angle, relative) - Set heading in degrees

STATUS/INFO:
- get_battery() - Get battery status
- get_position() - Get GPS position
- get_mode() - Get current flight mode
- is_armable() - Check if ready to arm

PARAMETER CONFIGURATION (NEW!):
- set_parameter(param_name, value) - Set ArduPilot parameter
- get_parameter(param_name) - Get parameter value

EMERGENCY:
- emergency_stop() - Emergency motor stop (USE WITH CAUTION!)

MISSION PLANNING:
- create_mission() - Start new mission
- add_takeoff_waypoint(altitude) - Add takeoff to mission
- add_waypoint(lat, lon, alt) - Add GPS waypoint
- add_land_waypoint() - Add land to mission
- upload_mission() - Upload mission to drone
- start_mission() - Start mission execution
- clear_mission() - Clear mission

Examples:
"arm the drone" → {"function": "arm", "parameters": {}}
"arm and takeoff to 15 meters" → {"function": "arm_and_takeoff", "parameters": {"altitude": 15}}
"takeoff to 15 meters" → {"function": "takeoff", "parameters": {"altitude": 15}}
"hold position for 5 seconds" → {"function": "hover", "parameters": {"duration": 5}}
"check battery" → {"function": "get_battery", "parameters": {}}
"change mode to GUIDED" → {"function": "change_mode", "parameters": {"mode": "GUIDED"}}
"set waypoint speed to 500" → {"function": "set_parameter", "parameters": {"param_name": "WPNAV_SPEED", "value": 500}}
"get waypoint speed" → {"function": "get_parameter", "parameters": {"param_name": "WPNAV_SPEED"}}
"get RTL altitude parameter" → {"function": "get_parameter", "parameters": {"param_name": "RTL_ALT"}}
"what is WPNAV_SPEED" → {"function": "get_parameter", "parameters": {"param_name": "WPNAV_SPEED"}}

Respond with ONLY the JSON object, nothing else."""
    
    def get_function_call(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Get function call from user input using Qwen 2.5
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Dictionary with function_name and arguments, or None if parsing failed
        """
        try:
            # Build prompt with system context
            prompt = f"""{self.system_prompt}

Command: "{user_input}"

JSON:"""
            
            # Call Qwen 2.5
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.1,
                    'num_predict': 100
                }
            )
            
            # Get response content
            raw_response = response['response'].strip()
            
            # Extract JSON from response
            result = self._extract_json(raw_response)
            
            if result:
                # Convert to internal format
                function_name = result.get('function')
                parameters = result.get('parameters', {})
                
                print(f"[PARSED] {function_name}({parameters})")
                
                return {
                    "function_name": function_name,
                    "arguments": parameters
                }
            else:
                print(f"[ERROR] Could not parse function call from: {raw_response}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error communicating with model: {e}")
            return None
    
    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from model response
        
        Args:
            content: Raw response from model
            
        Returns:
            Parsed JSON dict or None
        """
        try:
            # Try markdown code block first
            if "```json" in content:
                json_match = re.search(r'```json\s*(\{.+?\})\s*```', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1).strip())
            
            # Try direct JSON extraction
            json_match = re.search(r'\{.+\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group().strip())
            
            return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON decode error: {e}")
            return None
    
    def query(self, user_input: str) -> Dict[str, Any]:
        """
        Query for backward compatibility with demo.py
        Returns format: {'type': 'function_calls', 'calls': [{'name': ..., 'arguments': ...}]}
        """
        result = self.get_function_call(user_input)
        
        if result:
            return {
                'type': 'function_calls',
                'calls': [{
                    'name': result['function_name'],
                    'arguments': result['arguments']
                }]
            }
        else:
            return {
                'type': 'text',
                'content': 'Could not understand command'
            }
    
    def format_result_message(self, function_name: str, result: Dict[str, Any]) -> str:
        """
        Format function result into a user-friendly message.
        
        Special formatting for data-returning functions like get_battery and get_position.
        
        Args:
            function_name: Name of the function that was executed
            result: Result dictionary from function execution
            
        Returns:
            Formatted message string for display to user
        """
        if result.get('status') != 'success':
            return result.get('message', 'Command failed')
        
        # Special formatting for battery status
        if function_name == 'get_battery':
            voltage = result.get('voltage', 0.0)
            current = result.get('current', 0.0)
            remaining = result.get('remaining', 0)
            return f"Battery: {voltage:.2f}V, {current:.2f}A, {remaining}% remaining"
        
        # Special formatting for position
        elif function_name == 'get_position':
            lat = result.get('latitude', 0.0)
            lon = result.get('longitude', 0.0)
            alt = result.get('altitude', 0.0)
            heading = result.get('heading', 0.0)
            return f"Position: Lat {lat:.6f}°, Lon {lon:.6f}°, Alt {alt:.1f}m, Heading {heading:.1f}°"
        
        # Special formatting for mode
        elif function_name == 'get_mode':
            mode = result.get('mode', 'UNKNOWN')
            return f"Current mode: {mode}"
        
        # Special formatting for armable status
        elif function_name == 'is_armable':
            armable = result.get('armable', False)
            reasons = result.get('reasons', [])
            if armable:
                return "Drone is ready to arm"
            else:
                reason_text = ", ".join(reasons) if reasons else "Unknown reasons"
                return f"WARNING: Drone not ready to arm: {reason_text}"
        
        # Default: use the message from result
        return result.get('message', 'Command executed successfully')
    
    def add_tool_result(self, function_name: str, result: Dict[str, Any]) -> str:
        """
        Format tool result as response message.
        For backward compatibility with demo.py and main.py
        
        Args:
            function_name: Name of the function that was executed
            result: Result dictionary from function execution
            
        Returns:
            Formatted message string for display to user
        """
        return self.format_result_message(function_name, result)
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []


# Backward compatibility aliases
FunctionGemmaInterface = Qwen25Interface


def get_function_from_gemma(user_input: str, model_name: str = "qwen2.5:3b") -> Optional[Dict[str, Any]]:
    """
    Legacy function - Get function call from model
    
    Args:
        user_input: User's natural language command
        model_name: Ollama model name
        
    Returns:
        Dict with function_name and arguments, or None
    """
    interface = Qwen25Interface(model_name)
    return interface.get_function_call(user_input)
