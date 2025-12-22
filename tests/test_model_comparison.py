#!/usr/bin/env python3
"""
Model Comparison Test Script

Tests different models (Gemma 3, Qwen 2.5, FunctionGemma) with the same command set
and compares accuracy, response time, and output quality.
"""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.model_adapter import get_model_adapter


# Test commands with expected function calls
TEST_CASES = [
    # Basic commands
    ("arm the drone", "arm", {}),
    ("disarm", "disarm", {}),
    ("land", "land", {}),
    ("return to launch", "rtl", {}),
    
    # Commands with parameters
    ("takeoff to 15 meters", "takeoff", {"altitude": 15}),
    ("takeoff 20", "takeoff", {"altitude": 20}),
    ("takeoff drone at 25", "takeoff", {"altitude": 25}),
    
    # Mode changes
    ("change mode to GUIDED", "change_mode", {"mode": "GUIDED"}),
    ("switch to LOITER mode", "change_mode", {"mode": "LOITER"}),
    
    # Status queries
    ("check battery", "get_battery", {}),
    ("battery status", "get_battery", {}),
    ("where am I", "get_position", {}),
    ("current position", "get_position", {}),
    
    # Natural variations
    ("arm", "arm", {}),
    ("take off to 10 meters", "takeoff", {"altitude": 10}),
    ("go to GUIDED mode", "change_mode", {"mode": "GUIDED"}),
]


def test_model(model_name: str) -> dict:
    """
    Test a model with all test cases
    
    Returns:
        dict with results
    """
    print(f"\n{'='*70}")
    print(f"Testing Model: {model_name.upper()}")
    print('='*70)
    
    adapter = get_model_adapter(model_name)
    
    results = {
        "model": model_name,
        "total": len(TEST_CASES),
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "total_time": 0,
        "avg_time": 0,
        "details": []
    }
    
    for i, (command, expected_func, expected_params) in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Testing: '{command}'")
        
        start_time = time.time()
        try:
            result = adapter.get_function_call(command)
            elapsed = time.time() - start_time
            results["total_time"] += elapsed
            
            if result is None:
                print(f"  ❌ FAIL: No result returned")
                results["failed"] += 1
                results["details"].append({
                    "command": command,
                    "status": "FAIL",
                    "reason": "No result",
                    "time": elapsed
                })
                continue
            
            # Check function name
            actual_func = result.get("function", "")
            actual_params = result.get("parameters", {})
            
            func_match = actual_func == expected_func
            params_match = actual_params == expected_params
            
            if func_match and params_match:
                print(f"  ✅ PASS: {result} ({elapsed:.3f}s)")
                results["passed"] += 1
                results["details"].append({
                    "command": command,
                    "status": "PASS",
                    "result": result,
                    "time": elapsed
                })
            else:
                print(f"  ❌ FAIL: Got {result}, expected {expected_func}({expected_params})")
                results["failed"] += 1
                results["details"].append({
                    "command": command,
                    "status": "FAIL",
                    "expected": {"function": expected_func, "parameters": expected_params},
                    "actual": result,
                    "time": elapsed
                })
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ ERROR: {e}")
            results["errors"] += 1
            results["total_time"] += elapsed
            results["details"].append({
                "command": command,
                "status": "ERROR",
                "error": str(e),
                "time": elapsed
            })
    
    results["avg_time"] = results["total_time"] / len(TEST_CASES) if TEST_CASES else 0
    results["accuracy"] = (results["passed"] / len(TEST_CASES) * 100) if TEST_CASES else 0
    
    return results


def print_summary(all_results: list):
    """Print comparison summary"""
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    print(f"\n{'Model':<20} {'Accuracy':<12} {'Avg Time':<12} {'Passed':<10}")
    print("-" * 70)
    
    for result in all_results:
        accuracy = f"{result['accuracy']:.1f}%"
        avg_time = f"{result['avg_time']:.3f}s"
        passed = f"{result['passed']}/{result['total']}"
        
        print(f"{result['model']:<20} {accuracy:<12} {avg_time:<12} {passed:<10}")
    
    # Find best model
    best_accuracy = max(all_results, key=lambda x: x['accuracy'])
    fastest = min(all_results, key=lambda x: x['avg_time'])
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    print(f"Best Accuracy: {best_accuracy['model']} ({best_accuracy['accuracy']:.1f}%)")
    print(f"Fastest: {fastest['model']} ({fastest['avg_time']:.3f}s avg)")
    
    # Overall recommendation
    print("\nOverall Recommendation:")
    if best_accuracy['model'] == fastest['model']:
        print(f"  ✅ {best_accuracy['model']} - Best accuracy AND fastest!")
    else:
        print(f"  ✅ {best_accuracy['model']} - For maximum accuracy")
        print(f"  ⚡ {fastest['model']} - For fastest response")


def main():
    """Main test function"""
    print("="*70)
    print("MODEL COMPARISON TEST")
    print("="*70)
    print(f"\nTesting {len(TEST_CASES)} commands across multiple models...")
    
    models_to_test = ["functiongemma", "qwen2.5", "gemma3"]
    all_results = []
    
    for model in models_to_test:
        try:
            results = test_model(model)
            all_results.append(results)
        except Exception as e:
            print(f"\n❌ Failed to test {model}: {e}")
    
    if all_results:
        print_summary(all_results)
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
