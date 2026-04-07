#!/usr/bin/env python3
"""
ArduPilot AI Model Comparison & Benchmarking Suite

Tests different Ollama models via the active REST API.
Evaluates:
1. Accuracy (Did it extract the correct JSON command?)
2. Latency (Response time in seconds)
3. "Chattiness" (Are there <think> tokens or excessive explanation breaking regex?)
"""

import time
import requests
import json
import sys
from prettytable import PrettyTable

# The active backend server
API_URL = "http://localhost:5000/chat"
HEALTH_URL = "http://localhost:5000/status"

# Models to benchmark: You can edit this list if you pull new models!
MODELS_TO_TEST = [
    "qwen2.5:3b",
    "gemma2:2b", # Currently highly recommended over Qwen
    "llama3.2:3b",
    "test_bot_fixed"
]

TEST_CASES = [
    # (User Prompt, Expected Command Type, Expected Params)
    ("arm the drone", "ARM", {}),
    ("take off to 15 meters", "TAKEOFF", {"altitude": 15}),
    ("land right now", "LAND", {}),
    ("return to launch", "RTL", {}),
    ("change flight mode to LOITER", "CHANGE_MODE", {"mode": "LOITER"}),
    ("move north 20m", "MOVE_DIRECTION", {"direction": "north", "distance": 20}),
    ("set parameter WPNAV_SPEED to 500", "SET_PARAM", {"param_id": "WPNAV_SPEED", "value": 500.0}),
    ("go to battery failsafe params", "SEARCH_PARAM", {"query": "battery failsafe"}) # Pending new architecture!
]

def check_backend():
    try:
        r = requests.get(HEALTH_URL)
        if r.status_code == 200:
            return r.json().get("available_models", [])
        return []
    except:
        return []

def run_benchmarks(available_models):
    print("=" * 80)
    print("🚀 ARDUPILOT AI: MODEL BENCHMARKING SUITE")
    print("=" * 80)

    # Force testing all requested models instead of checking backend cache
    active_models = MODELS_TO_TEST
    
    if not active_models:
        print("❌ Error: None of the target models are currently loaded in Ollama.")
        print(f"Required targets: {MODELS_TO_TEST}")
        sys.exit(1)

    print(f"Testing models: {active_models}\n")
    
    results = {}

    for model in active_models:
        print(f"--- Running tests for {model} ---")
        passed = 0
        total_latency = 0
        overthinking_count = 0
        
        for case in TEST_CASES:
            prompt, expected_type, expected_params = case
            payload = {
                "message": prompt,
                "mode": "agent",
                "model": model,
                "telemetry": {
                    "status": {"mode": "STABILIZE", "armed": False},
                    "gps": {"satellites": 12, "altitude": 0}
                }
            }
            
            start_time = time.time()
            try:
                r = requests.post(API_URL, json=payload, timeout=20)
                latency = time.time() - start_time
                data = r.json()
            except requests.exceptions.RequestException:
                print(f"  [Error] API timeout or crash for '{prompt}'")
                continue

            total_latency += latency
            
            # Check accuracy
            is_accurate = False
            if data.get("success") and data.get("command"):
                cmd = data["command"]
                # For some test cases like SEARCH_PARAM which might not exist in backend yet, we gracefully ignore failure mapping
                if cmd.get("type") == expected_type:
                    is_accurate = True
            
            if is_accurate: passed += 1

            # Check for Chattiness/Overthinking
            ai_text = data.get("response") or ""
            if len(ai_text.split()) > 15 or "<think>" in ai_text:
                overthinking_count += 1
                
        # Store results
        results[model] = {
            "accuracy": (passed / len(TEST_CASES)) * 100,
            "latency": total_latency / len(TEST_CASES),
            "chattiness": (overthinking_count / len(TEST_CASES)) * 100
        }

    # Print Report
    print("\n" + "=" * 80)
    print("📊 BENCHMARK REPORT")
    print("=" * 80)
    
    pt = PrettyTable()
    pt.field_names = ["Model", "Accuracy", "Avg Latency", "Overthinking Rate"]
    
    for model, res in results.items():
        acc = f"{res['accuracy']:.1f}%"
        lat = f"{res['latency']:.2f}s"
        chat = f"{res['chattiness']:.1f}%"
        pt.add_row([model, acc, lat, chat])
        
    print(pt)
    print("\n💡 Insights:")
    print("- High Accuracy (>90%) means the model understands commands perfectly.")
    print("- Low Avg Latency (<2.0s) is critical for real-time drone control.")
    print("- High Overthinking Rate means the model is outputting <think> blocks or chatting too much, slowing down extraction.")

if __name__ == "__main__":
    avail = check_backend()
    if not avail:
        print("❌ Backend is not running on http://localhost:5000. Please start it first.")
        sys.exit(1)
    run_benchmarks(avail)
