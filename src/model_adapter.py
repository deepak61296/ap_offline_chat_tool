"""
Model Adapter Interface for Alternative Models

This module provides adapters for different LLM models to replace FunctionGemma.
Supports: Gemma 3, Qwen 2.5, and other instruction-following models.
"""

import json
import re
from typing import Dict, Any, Optional
import ollama


class ModelAdapter:
    """Base class for model adapters"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with function definitions"""
        return """You are an ArduPilot drone assistant. You translate natural language commands into function calls.

Available functions:
1. arm() - Arm the drone motors
2. disarm() - Disarm the drone motors
3. takeoff(altitude: number) - Take off to specified altitude in meters
4. land() - Land at current location
5. rtl() - Return to launch position
6. change_mode(mode: string) - Change flight mode (GUIDED, LOITER, RTL, LAND, STABILIZE, AUTO)
7. get_battery() - Get battery status
8. get_position() - Get GPS position

Respond ONLY with a JSON object in this format:
{"function": "function_name", "parameters": {...}}

Examples:
User: "arm the drone"
{"function": "arm", "parameters": {}}

User: "takeoff to 15 meters"
{"function": "takeoff", "parameters": {"altitude": 15}}

User: "check battery"
{"function": "get_battery", "parameters": {}}

User: "change mode to GUIDED"
{"function": "change_mode", "parameters": {"mode": "GUIDED"}}

Respond ONLY with valid JSON. No explanations."""

    def get_function_call(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Get function call from user input
        
        Args:
            user_input: Natural language command
            
        Returns:
            Dict with function name and parameters, or None if parsing fails
        """
        raise NotImplementedError("Subclasses must implement get_function_call")


class Gemma3Adapter(ModelAdapter):
    """Adapter for Gemma 3 (4B parameters)"""
    
    def __init__(self):
        super().__init__("gemma3:4b")
    
    def get_function_call(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Get function call using Gemma 3"""
        try:
            # Enhanced prompt for better JSON output
            prompt = f"""Convert this drone command to a JSON function call.

Available functions:
- arm() - Arm drone
- disarm() - Disarm drone  
- takeoff(altitude) - Takeoff to altitude in meters
- land() - Land drone
- rtl() - Return to launch
- change_mode(mode) - Change flight mode
- get_battery() - Get battery status
- get_position() - Get GPS position

Command: "{user_input}"

Respond ONLY with JSON in this exact format:
{{"function": "function_name", "parameters": {{}}}}

JSON:"""

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.1,
                    "num_predict": 100
                }
            )
            
            # Extract JSON from response
            content = response['response'].strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return result
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Gemma3 parsing failed: {e}")
            return None


class Qwen25Adapter(ModelAdapter):
    """Adapter for Qwen 2.5 (3B parameters)"""
    
    def __init__(self):
        super().__init__("qwen2.5:3b")
    
    def get_function_call(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Get function call using Qwen 2.5"""
        try:
            # Qwen works better with chat format
            prompt = f"""You are a drone command parser. Convert commands to JSON.

Available functions:
- arm() - Arm drone motors
- disarm() - Disarm drone motors
- takeoff(altitude) - Takeoff to altitude in meters
- land() - Land at current location
- rtl() - Return to launch
- change_mode(mode) - Change flight mode (GUIDED, LOITER, RTL, LAND)
- get_battery() - Get battery status
- get_position() - Get GPS position

Examples:
"arm the drone" → {{"function": "arm", "parameters": {{}}}}
"takeoff to 15 meters" → {{"function": "takeoff", "parameters": {{"altitude": 15}}}}
"check battery" → {{"function": "get_battery", "parameters": {{}}}}

Command: "{user_input}"

Respond with ONLY the JSON object, nothing else:"""

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.1,
                    "num_predict": 100
                }
            )
            
            # Extract JSON from response
            content = response['response'].strip()
            
            # Qwen often wraps JSON in markdown code blocks
            if "```json" in content:
                json_match = re.search(r'```json\s*(\{[^`]+\})\s*```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    return result
            
            # Try to find JSON directly
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return result
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Qwen2.5 parsing failed: {e}")
            print(f"[DEBUG] Response was: {content if 'content' in locals() else 'N/A'}")
            return None


class FunctionGemmaAdapter(ModelAdapter):
    """Adapter for original FunctionGemma (270M parameters)"""
    
    def __init__(self):
        super().__init__("deepakpopli/ardupilot-stage1")
    
    def get_function_call(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Get function call using FunctionGemma (original implementation)"""
        try:
            # FunctionGemma uses a different format
            response = ollama.generate(
                model=self.model_name,
                prompt=user_input,
                options={
                    "temperature": 0.1,
                    "num_predict": 50
                }
            )
            
            output = response['response'].strip()
            
            # Parse FunctionGemma output format
            if '(' in output and ')' in output:
                func_name = output.split('(')[0].strip()
                params_str = output.split('(')[1].split(')')[0]
                
                # Parse parameters
                params = {}
                if params_str and params_str != '{}':
                    # Simple parameter parsing
                    for param in params_str.split(','):
                        if ':' in param:
                            key, value = param.split(':', 1)
                            key = key.strip().strip('"\'')
                            value = value.strip().strip('"\'')
                            try:
                                params[key] = float(value) if '.' in value else int(value)
                            except:
                                params[key] = value
                
                return {"function": func_name, "parameters": params}
            
            return None
            
        except Exception as e:
            print(f"[ERROR] FunctionGemma parsing failed: {e}")
            return None


def get_model_adapter(model_name: str) -> ModelAdapter:
    """
    Factory function to get appropriate model adapter
    
    Args:
        model_name: Name of the model (gemma3, qwen2.5, functiongemma)
        
    Returns:
        ModelAdapter instance
    """
    adapters = {
        "gemma3": Gemma3Adapter,
        "qwen2.5": Qwen25Adapter,
        "functiongemma": FunctionGemmaAdapter
    }
    
    adapter_class = adapters.get(model_name.lower())
    if not adapter_class:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(adapters.keys())}")
    
    return adapter_class()


if __name__ == "__main__":
    # Quick test
    print("Testing model adapters...")
    
    test_commands = [
        "arm the drone",
        "takeoff to 15 meters",
        "check battery status",
        "change mode to GUIDED"
    ]
    
    for model_name in ["gemma3", "qwen2.5", "functiongemma"]:
        print(f"\n{'='*60}")
        print(f"Testing: {model_name}")
        print('='*60)
        
        adapter = get_model_adapter(model_name)
        
        for cmd in test_commands:
            print(f"\nCommand: {cmd}")
            result = adapter.get_function_call(cmd)
            print(f"Result: {result}")
