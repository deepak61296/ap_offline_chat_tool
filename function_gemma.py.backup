"""
FunctionGemma Interface
Handles communication with FunctionGemma model via Ollama
"""

import json
import re
from typing import Dict, List, Any, Optional
from ollama import chat
from drone_functions import DRONE_FUNCTIONS


class FunctionGemmaInterface:
    """Interface for FunctionGemma model via Ollama"""
    
    def __init__(self, model: str = 'functiongemma'):
        """
        Initialize FunctionGemma interface
        
        Args:
            model: Ollama model name (default: functiongemma)
        """
        self.model = model
        self.conversation_history = []
        self.tools = self._prepare_tools()
        
    def _prepare_tools(self) -> List[Dict]:
        """
        Convert DRONE_FUNCTIONS to Ollama tools format
        
        Returns:
            List of tool definitions in Ollama format
        """
        tools = []
        for func_name, func_def in DRONE_FUNCTIONS.items():
            tool = {
                "type": "function",
                "function": {
                    "name": func_def["name"],
                    "description": func_def["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Add parameters if they exist
            if func_def["parameters"]:
                for param_name, param_info in func_def["parameters"].items():
                    tool["function"]["parameters"]["properties"][param_name] = {
                        "type": param_info["type"],
                        "description": param_info["description"]
                    }
                    if param_info.get("required", False):
                        tool["function"]["parameters"]["required"].append(param_name)
            
            tools.append(tool)
        
        return tools
    
    def query(self, user_message: str) -> Dict[str, Any]:
        """
        Send query to FunctionGemma and get response
        
        Args:
            user_message: User's natural language command
        
        Returns:
            Dictionary containing function calls or text response
        """
        # Add user message to history
        self.conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        print(f"\n🤖 Querying FunctionGemma...")
        print(f"📝 User: {user_message}")
        
        try:
            # Call FunctionGemma via Ollama
            response = chat(
                model=self.model,
                messages=self.conversation_history,
                tools=self.tools
            )
            
            # Check if model wants to call functions
            if hasattr(response.message, 'tool_calls') and response.message.tool_calls:
                print(f"🔧 FunctionGemma wants to call {len(response.message.tool_calls)} function(s)")
                
                function_calls = []
                for tool_call in response.message.tool_calls:
                    func_info = {
                        'name': tool_call.function.name,
                        'arguments': tool_call.function.arguments
                    }
                    function_calls.append(func_info)
                    print(f"   → {func_info['name']}({func_info['arguments']})")
                
                # Add assistant's tool call to history
                self.conversation_history.append(response.message)
                
                return {
                    'type': 'function_calls',
                    'calls': function_calls
                }
            else:
                # Pure text response
                text_response = response.message.content
                print(f"💬 FunctionGemma: {text_response}")
                
                # Add to history
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': text_response
                })
                
                return {
                    'type': 'text',
                    'content': text_response
                }
                
        except Exception as e:
            error_msg = f"Error querying FunctionGemma: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'type': 'error',
                'message': error_msg
            }
    
    def add_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """
        Add function execution result back to conversation
        
        Args:
            tool_name: Name of the executed function
            result: Result dictionary from function execution
        
        Returns:
            Final natural language response from FunctionGemma
        """
        # Add tool result to history
        self.conversation_history.append({
            'role': 'tool',
            'content': json.dumps(result)
        })
        
        print(f"\n🔄 Sending function result back to FunctionGemma...")
        
        try:
            # Get final response from model
            final_response = chat(
                model=self.model,
                messages=self.conversation_history
            )
            
            final_text = final_response.message.content
            print(f"💬 FunctionGemma: {final_text}")
            
            # Add final response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': final_text
            })
            
            return final_text
            
        except Exception as e:
            error_msg = f"Error getting final response: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🔄 Conversation history cleared")


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("FunctionGemma Interface Test")
    print("=" * 60)
    
    # Create interface
    gemma = FunctionGemmaInterface()
    
    # Test queries
    test_queries = [
        "Take off to 10 meters",
        "What's my current position?",
        "Change mode to LOITER",
        "Fly to latitude 28.5, longitude 77.0 at 20 meters altitude"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Test Query: {query}")
        print(f"{'='*60}")
        
        response = gemma.query(query)
        print(f"\nResponse Type: {response['type']}")
        print(f"Response Content: {response}")
        
        # Reset for next test
        gemma.reset_conversation()
        print()
