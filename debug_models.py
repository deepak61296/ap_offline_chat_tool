#!/usr/bin/env python3
"""Quick debug script to see what models actually return"""

import ollama

print("Testing what models actually return...\n")

# Test command
command = "arm the drone"

# Test Qwen 2.5
print("="*60)
print("Testing Qwen 2.5 (3B)")
print("="*60)
try:
    response = ollama.chat(
        model='qwen2.5:3b',
        messages=[
            {'role': 'user', 'content': f'Convert this to JSON function call: {command}'}
        ]
    )
    print(f"Response: {response['message']['content']}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test Gemma 3
print("="*60)
print("Testing Gemma 3 (4B)")
print("="*60)
try:
    response = ollama.chat(
        model='gemma3:4b',
        messages=[
            {'role': 'user', 'content': f'Convert this to JSON function call: {command}'}
        ]
    )
    print(f"Response: {response['message']['content']}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test FunctionGemma
print("="*60)
print("Testing FunctionGemma (270M)")
print("="*60)
try:
    response = ollama.generate(
        model='deepakpopli/ardupilot-stage1',
        prompt=command
    )
    print(f"Response: {response['response']}")
except Exception as e:
    print(f"Error: {e}")
