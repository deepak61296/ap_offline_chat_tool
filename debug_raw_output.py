#!/usr/bin/env python3
"""
Debug script to see exactly what models return
"""

import ollama

command = "arm the drone"

print("="*70)
print("DEBUGGING MODEL OUTPUTS")
print("="*70)

# Test Gemma 3
print("\n" + "="*70)
print("Gemma 3 (4B) - Raw Output")
print("="*70)
prompt = f"""Convert this drone command to a JSON function call.

Available functions:
- arm() - Arm drone
- takeoff(altitude) - Takeoff to altitude in meters
- get_battery() - Get battery status

Command: "{command}"

Respond ONLY with JSON in this exact format:
{{"function": "function_name", "parameters": {{}}}}

JSON:"""

response = ollama.generate(model='gemma3:4b', prompt=prompt, options={'temperature': 0.1})
print(f"Raw response:\n{response['response']}")
print(f"\nStripped:\n{response['response'].strip()}")

# Test Qwen 2.5
print("\n" + "="*70)
print("Qwen 2.5 (3B) - Raw Output")
print("="*70)
response = ollama.generate(model='qwen2.5:3b', prompt=prompt, options={'temperature': 0.1})
print(f"Raw response:\n{response['response']}")
print(f"\nStripped:\n{response['response'].strip()}")

# Test FunctionGemma
print("\n" + "="*70)
print("FunctionGemma (270M) - Raw Output")
print("="*70)
response = ollama.generate(model='deepakpopli/ardupilot-stage1', prompt=command, options={'temperature': 0.1})
print(f"Raw response:\n{response['response']}")
print(f"\nStripped:\n{response['response'].strip()}")
