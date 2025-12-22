#!/usr/bin/env python3
"""
Test preprocessing functionality for takeoff commands
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.qwen_interface import Qwen25Interface as FunctionGemmaInterface

def test_preprocessing():
    """Test that preprocessing converts variations correctly"""
    
    gemma = FunctionGemmaInterface()
    
    test_cases = [
        # (input, expected_output)
        ("takeoff 20", "takeoff to 20 meters"),
        ("takeoff drone 20", "takeoff to 20 meters"),
        ("takeoff drone at 29", "takeoff to 29 meters"),
        ("takeoff at 15", "takeoff to 15 meters"),
        ("take off 20", "takeoff to 20 meters"),
        ("take off drone 20", "takeoff to 20 meters"),
        ("takeoff 15 meters", "takeoff to 15 meters"),
        ("takeoff 15m", "takeoff to 15 meters"),
        
        # Should not change these
        ("takeoff to 20 meters", "takeoff to 20 meters"),
        ("arm the drone", "arm the drone"),
        ("check battery", "check battery"),
    ]
    
    print("="*60)
    print("TESTING COMMAND PREPROCESSING")
    print("="*60)
    print()
    
    passed = 0
    failed = 0
    
    for input_cmd, expected in test_cases:
        result = gemma.preprocess_command(input_cmd)
        
        if result == expected:
            print(f"[PASS] '{input_cmd}' → '{result}'")
            passed += 1
        else:
            print(f"[FAIL] '{input_cmd}'")
            print(f"   Expected: '{expected}'")
            print(f"   Got:      '{result}'")
            failed += 1
    
    print()
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = test_preprocessing()
    sys.exit(0 if success else 1)
