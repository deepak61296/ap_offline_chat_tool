#!/usr/bin/env python3
"""
Standalone Model Comparison Test
Tests models directly without importing existing code
"""

import json
import re
import time
import ollama


def test_gemma3(command: str):
    """Test Gemma 3 model"""
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

Command: "{command}"

Respond ONLY with JSON in this exact format:
{{"function": "function_name", "parameters": {{}}}}

JSON:"""

    try:
        response = ollama.generate(
            model='gemma3:4b',
            prompt=prompt,
            options={'temperature': 0.1, 'num_predict': 100}
        )
        content = response['response'].strip()
        
        # Gemma 3 wraps in markdown code blocks
        if "```json" in content:
            json_match = re.search(r'```json\s*(\{.+?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                return json.loads(json_str)
        
        # Try direct JSON with better regex for nested braces
        json_match = re.search(r'\{.+\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group().strip()
            return json.loads(json_str)
        return None
    except Exception as e:
        print(f"Gemma3 error: {e}")
        print(f"Content was: {content if 'content' in locals() else 'N/A'}")
        return None


def test_qwen25(command: str):
    """Test Qwen 2.5 model"""
    prompt = f"""You are a drone command parser. Convert commands to JSON.

Available functions:
- arm() - Arm drone motors
- disarm() - Disarm drone motors
- takeoff(altitude) - Takeoff to altitude in meters
- land() - Land at current location
- rtl() - Return to launch
- change_mode(mode) - Change flight mode
- get_battery() - Get battery status
- get_position() - Get GPS position

Examples:
"arm the drone" → {{"function": "arm", "parameters": {{}}}}
"takeoff to 15 meters" → {{"function": "takeoff", "parameters": {{"altitude": 15}}}}

Command: "{command}"

Respond with ONLY the JSON object:"""

    try:
        response = ollama.generate(
            model='qwen2.5:3b',
            prompt=prompt,
            options={'temperature': 0.1, 'num_predict': 100}
        )
        content = response['response'].strip()
        
        # Try markdown code block first
        if "```json" in content:
            json_match = re.search(r'```json\s*(\{.+?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                return json.loads(json_str)
        
        # Try direct JSON with better regex
        json_match = re.search(r'\{.+\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group().strip()
            return json.loads(json_str)
        return None
    except Exception as e:
        print(f"Qwen2.5 error: {e}")
        print(f"Content was: {content if 'content' in locals() else 'N/A'}")
        return None


def test_functiongemma(command: str):
    """Test FunctionGemma model"""
    try:
        response = ollama.generate(
            model='deepakpopli/ardupilot-stage1',
            prompt=command,
            options={'temperature': 0.1, 'num_predict': 50}
        )
        output = response['response'].strip()
        
        if '(' in output and ')' in output:
            func_name = output.split('(')[0].strip()
            params_str = output.split('(')[1].split(')')[0]
            params = {}
            if params_str and params_str != '{}':
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
        print(f"FunctionGemma error: {e}")
        return None


# Test cases
TEST_CASES = [
    ("arm the drone", "arm", {}),
    ("takeoff to 15 meters", "takeoff", {"altitude": 15}),
    ("check battery", "get_battery", {}),
    ("land", "land", {}),
]

print("="*70)
print("MODEL COMPARISON TEST")
print("="*70)

for model_name, test_func in [("Gemma 3 (4B)", test_gemma3), 
                                ("Qwen 2.5 (3B)", test_qwen25),
                                ("FunctionGemma (270M)", test_functiongemma)]:
    print(f"\n{'='*70}")
    print(f"Testing: {model_name}")
    print('='*70)
    
    passed = 0
    total_time = 0
    
    for cmd, expected_func, expected_params in TEST_CASES:
        print(f"\nCommand: '{cmd}'")
        start = time.time()
        result = test_func(cmd)
        elapsed = time.time() - start
        total_time += elapsed
        
        if result and result.get("function") == expected_func and result.get("parameters") == expected_params:
            print(f"  ✅ PASS: {result} ({elapsed:.2f}s)")
            passed += 1
        else:
            print(f"  ❌ FAIL: Got {result}, expected {expected_func}({expected_params})")
    
    accuracy = (passed / len(TEST_CASES)) * 100
    avg_time = total_time / len(TEST_CASES)
    print(f"\nAccuracy: {accuracy:.1f}% ({passed}/{len(TEST_CASES)})")
    print(f"Avg Time: {avg_time:.3f}s")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
