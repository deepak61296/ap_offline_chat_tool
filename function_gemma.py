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
            # Call model (no tools parameter - using embedded template)
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': user_input
                    }
                ]
            )
            
            # Get response content
            raw_response = response['message']['content']
            
            # Parse function call
            result = self.parse_function_call(raw_response)
            
            if result:
                print(f"✅ Parsed: {result['function_name']}({result['arguments']})")
            else:
                print(f"❌ Could not parse function call from: {raw_response}")
                
            return result
            
        except Exception as e:
            print(f"❌ Error communicating with model: {e}")
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
    
    def add_tool_result(self, function_name: str, result: Dict[str, Any]) -> str:
        """
        Format tool result as response message
        For backward compatibility with demo.py
        """
        if result.get('status') == 'success':
            return result.get('message', 'Command executed successfully')
        else:
            return result.get('message', 'Command failed')
    
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
