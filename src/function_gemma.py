"""
FunctionGemma Communication Module
Handles communication with Ollama FunctionGemma model for drone control
"""

import ollama
import re
import json
from typing import Dict, Any, Optional

class FunctionGemmaInterface:
    """Interface for communicating with FunctionGemma via Ollama"""
    
    def __init__(self, model_name: str = "ardupilot-stage1"):
        """
        Initialize FunctionGemma interface
        
        Args:
            model_name: Name of the Ollama model to use (default: ardupilot-stage1)
        """
        self.model_name = model_name
        self.conversation_history = []
    
    def preprocess_command(self, user_input: str) -> str:
        """
        Preprocess user commands to fix common pattern variations.
        
        Converts natural variations to model-friendly format. This helps handle
        commands that weren't in the training data but are natural to say.
        
        Args:
            user_input: Raw user command
            
        Returns:
            Preprocessed command that the model can understand
            
        Example:
            >>> preprocess_command("takeoff 20")
            'takeoff to 20 meters'
            >>> preprocess_command("takeoff drone at 15")
            'takeoff to 15 meters'
        """
        import re
        
        processed = user_input.lower().strip()
        
        # Fix takeoff variations - convert to "takeoff to X meters"
        takeoff_patterns = [
            # "takeoff 20" → "takeoff to 20 meters"
            (r'\btakeoff\s+(\d+)\s*(?:meters?|m)?\s*$', r'takeoff to \1 meters'),
            
            # "takeoff drone 20" → "takeoff to 20 meters"
            (r'\btakeoff\s+drone\s+(\d+)\b', r'takeoff to \1 meters'),
            
            # "takeoff drone at 20" → "takeoff to 20 meters"
            (r'\btakeoff\s+drone\s+at\s+(\d+)\b', r'takeoff to \1 meters'),
            
            # "takeoff at 20" → "takeoff to 20 meters"
            (r'\btakeoff\s+at\s+(\d+)\b', r'takeoff to \1 meters'),
            
            # "take off 20" → "takeoff to 20 meters"
            (r'\btake\s+off\s+(\d+)\b', r'takeoff to \1 meters'),
            
            # "take off drone 20" → "takeoff to 20 meters"
            (r'\btake\s+off\s+drone\s+(\d+)\b', r'takeoff to \1 meters'),
        ]
        
        for pattern, replacement in takeoff_patterns:
            processed = re.sub(pattern, replacement, processed)
        
        return processed
        
    def parse_function_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse FunctionGemma response to extract function call
        
        Args:
            response: Raw response from model
            
        Returns:
            Dictionary with function_name and arguments, or None if no valid call
        """
        # Look for <start_function_call>call:function_name{args}<end_function_call>
        pattern = r'<start_function_call>call:(\w+)\{([^}]*)\}<end_function_call>'
        match = re.search(pattern, response)
        
        if not match:
            return None
            
        function_name = match.group(1)
        args_str = match.group(2)
        
        # Parse arguments
        arguments = {}
        if args_str:
            # Handle escaped strings like mode:<escape>GUIDED<escape>
            # Replace <escape> tags with quotes for JSON parsing
            args_str = args_str.replace('<escape>', '"')
            
            # Try to parse as JSON-like format
            try:
                # Handle simple key:value pairs
                pairs = args_str.split(',')
                for pair in pairs:
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"')
                        
                        # Try to convert to appropriate type
                        try:
                            # Try integer
                            arguments[key] = int(value)
                        except ValueError:
                            try:
                                # Try float
                                arguments[key] = float(value)
                            except ValueError:
                                # Keep as string
                                arguments[key] = value
            except Exception as e:
                print(f"Warning: Could not parse arguments: {e}")
                print(f"Raw args: {args_str}")
        
        return {
            "function_name": function_name,
            "arguments": arguments
        }
    
    def get_function_call(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Get function call from user input
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Dictionary with function_name and arguments, or None if parsing failed
        """
        try:
            # Preprocess the input to fix common variations
            processed_input = self.preprocess_command(user_input)
            
            # Show preprocessing if input was changed
            if processed_input != user_input.lower().strip():
                print(f"[PREPROCESSED] '{user_input}' -> '{processed_input}'")
            
            # Call model (no tools parameter - using embedded template)
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': processed_input
                    }
                ]
            )
            
            # Get response content
            raw_response = response['message']['content']
            
            # Parse function call
            result = self.parse_function_call(raw_response)
            
            if result:
                print(f"[PARSED] {result['function_name']}({result['arguments']})")
            else:
                print(f"[ERROR] Could not parse function call from: {raw_response}")
                
            return result
            
        except Exception as e:
            print(f"[ERROR] Error communicating with model: {e}")
            return None
    
    def query(self, user_input: str) -> Dict[str, Any]:
        """
        Query for backward compatibility with demo.py
        Returns format: {'type': 'function_calls', 'calls': [{'name': ..., 'arguments': ...}]}
        """
        result = self.get_function_call(user_input)
        
        if result:
            # Convert to old format with 'name' key
            return {
                'type': 'function_calls',
                'calls': [{
                    'name': result['function_name'],  # Changed from 'function' to 'name'
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


# For backward compatibility
def get_function_from_gemma(user_input: str, model_name: str = "ardupilot-stage1") -> Optional[Dict[str, Any]]:
    """
    Legacy function - Get function call from FunctionGemma
    
    Args:
        user_input: User's natural language command
        model_name: Ollama model name
        
    Returns:
        Dict with function_name and arguments, or None
    """
    interface = FunctionGemmaInterface(model_name)
    return interface.get_function_call(user_input)
