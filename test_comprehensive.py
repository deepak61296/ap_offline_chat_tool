#!/usr/bin/env python3
"""
Comprehensive Model Comparison Test Suite
Tests models with natural language variations and generates CSV report
"""

import json
import re
import time
import csv
from datetime import datetime
import ollama


# Comprehensive test cases with natural language variations
TEST_CASES = [
    # ARM commands - various natural phrasings
    ("arm the drone", "arm", {}),
    ("please arm the drone", "arm", {}),
    ("can you arm the UAV", "arm", {}),
    ("hey arm it", "arm", {}),
    ("prepare for flight", "arm", {}),
    ("get ready to fly", "arm", {}),
    
    # DISARM commands
    ("disarm the drone", "disarm", {}),
    ("please disarm", "disarm", {}),
    ("shut down motors", "disarm", {}),
    ("turn off the drone", "disarm", {}),
    
    # TAKEOFF commands - lots of variations
    ("takeoff to 15 meters", "takeoff", {"altitude": 15}),
    ("take off to 20 meters", "takeoff", {"altitude": 20}),
    ("please takeoff to 10 meters", "takeoff", {"altitude": 10}),
    ("can you takeoff to 25 meters", "takeoff", {"altitude": 25}),
    ("hey takeoff the UAV to 30 meters", "takeoff", {"altitude": 30}),
    ("lift off to 12 meters", "takeoff", {"altitude": 12}),
    ("ascend to 18 meters", "takeoff", {"altitude": 18}),
    ("go up to 22 meters", "takeoff", {"altitude": 22}),
    ("fly to 15 meters altitude", "takeoff", {"altitude": 15}),
    ("takeoff 20", "takeoff", {"altitude": 20}),
    ("takeoff drone at 25", "takeoff", {"altitude": 25}),
    ("take off 10m", "takeoff", {"altitude": 10}),
    
    # LAND commands
    ("land the drone", "land", {}),
    ("please land", "land", {}),
    ("can you land now", "land", {}),
    ("bring it down", "land", {}),
    ("descend and land", "land", {}),
    ("touch down", "land", {}),
    
    # RTL commands
    ("return to launch", "rtl", {}),
    ("go back home", "rtl", {}),
    ("return home", "rtl", {}),
    ("come back to start", "rtl", {}),
    ("RTL please", "rtl", {}),
    
    # MODE CHANGE commands
    ("change mode to GUIDED", "change_mode", {"mode": "GUIDED"}),
    ("switch to LOITER mode", "change_mode", {"mode": "LOITER"}),
    ("set mode to RTL", "change_mode", {"mode": "RTL"}),
    ("go to GUIDED", "change_mode", {"mode": "GUIDED"}),
    ("enter LOITER mode", "change_mode", {"mode": "LOITER"}),
    ("change to LAND mode", "change_mode", {"mode": "LAND"}),
    
    # BATTERY status
    ("check battery", "get_battery", {}),
    ("battery status", "get_battery", {}),
    ("how much battery left", "get_battery", {}),
    ("what's the battery level", "get_battery", {}),
    ("show me battery", "get_battery", {}),
    ("battery info", "get_battery", {}),
    
    # POSITION queries
    ("where am I", "get_position", {}),
    ("current position", "get_position", {}),
    ("what's my location", "get_position", {}),
    ("show position", "get_position", {}),
    ("GPS coordinates", "get_position", {}),
    ("where is the drone", "get_position", {}),
]


def test_qwen25(command: str):
    """Test Qwen 2.5 model"""
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

Command: "{command}"

Respond with ONLY the JSON object:"""

    try:
        response = ollama.generate(
            model='qwen2.5:3b',
            prompt=prompt,
            options={'temperature': 0.1, 'num_predict': 100}
        )
        content = response['response'].strip()
        
        if "```json" in content:
            json_match = re.search(r'```json\s*(\{.+?\})\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1).strip())
        
        json_match = re.search(r'\{.+\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group().strip())
        return None
    except Exception as e:
        return None


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
        
        if "```json" in content:
            json_match = re.search(r'```json\s*(\{.+?\})\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1).strip())
        
        json_match = re.search(r'\{.+\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group().strip())
        return None
    except Exception as e:
        return None


def test_ardupilot_stage1(command: str):
    """Test ArduPilot Stage 1 (fine-tuned FunctionGemma)"""
    try:
        response = ollama.generate(
            model='deepakpopli/ardupilot-stage1',
            prompt=command,
            options={'temperature': 0.1, 'num_predict': 50}
        )
        output = response['response'].strip()
        
        # Parse FunctionGemma format: function_name({params})
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
        return None


def run_comprehensive_test():
    """Run comprehensive test and generate CSV report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"model_comparison_{timestamp}.csv"
    
    print("="*80)
    print("COMPREHENSIVE MODEL COMPARISON TEST")
    print("="*80)
    print(f"\nTesting {len(TEST_CASES)} natural language commands")
    print(f"Models: Qwen 2.5 (3B), Gemma 3 (4B), ArduPilot Stage 1 (270M)")
    print(f"\nResults will be saved to: {csv_filename}")
    print("="*80)
    
    # Prepare CSV
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['Command', 'Expected_Function', 'Expected_Params',
                     'Qwen25_Result', 'Qwen25_Correct', 'Qwen25_Time',
                     'Gemma3_Result', 'Gemma3_Correct', 'Gemma3_Time',
                     'ArduPilot_Result', 'ArduPilot_Correct', 'ArduPilot_Time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Statistics
        stats = {
            'qwen25': {'correct': 0, 'total': 0, 'total_time': 0},
            'gemma3': {'correct': 0, 'total': 0, 'total_time': 0},
            'ardupilot': {'correct': 0, 'total': 0, 'total_time': 0}
        }
        
        # Run tests
        for i, (command, expected_func, expected_params) in enumerate(TEST_CASES, 1):
            print(f"\n[{i}/{len(TEST_CASES)}] Testing: '{command}'")
            
            row = {
                'Command': command,
                'Expected_Function': expected_func,
                'Expected_Params': json.dumps(expected_params)
            }
            
            # Test Qwen 2.5
            start = time.time()
            qwen_result = test_qwen25(command)
            qwen_time = time.time() - start
            qwen_correct = (qwen_result and 
                           qwen_result.get('function') == expected_func and
                           qwen_result.get('parameters') == expected_params)
            
            row['Qwen25_Result'] = json.dumps(qwen_result) if qwen_result else 'FAIL'
            row['Qwen25_Correct'] = 'YES' if qwen_correct else 'NO'
            row['Qwen25_Time'] = f"{qwen_time:.3f}"
            stats['qwen25']['total'] += 1
            stats['qwen25']['total_time'] += qwen_time
            if qwen_correct:
                stats['qwen25']['correct'] += 1
                print(f"  Qwen 2.5: ✅ ({qwen_time:.2f}s)")
            else:
                print(f"  Qwen 2.5: ❌ ({qwen_time:.2f}s)")
            
            # Test Gemma 3
            start = time.time()
            gemma_result = test_gemma3(command)
            gemma_time = time.time() - start
            gemma_correct = (gemma_result and 
                            gemma_result.get('function') == expected_func and
                            gemma_result.get('parameters') == expected_params)
            
            row['Gemma3_Result'] = json.dumps(gemma_result) if gemma_result else 'FAIL'
            row['Gemma3_Correct'] = 'YES' if gemma_correct else 'NO'
            row['Gemma3_Time'] = f"{gemma_time:.3f}"
            stats['gemma3']['total'] += 1
            stats['gemma3']['total_time'] += gemma_time
            if gemma_correct:
                stats['gemma3']['correct'] += 1
                print(f"  Gemma 3:  ✅ ({gemma_time:.2f}s)")
            else:
                print(f"  Gemma 3:  ❌ ({gemma_time:.2f}s)")
            
            # Test ArduPilot Stage 1
            start = time.time()
            ardupilot_result = test_ardupilot_stage1(command)
            ardupilot_time = time.time() - start
            ardupilot_correct = (ardupilot_result and 
                                ardupilot_result.get('function') == expected_func and
                                ardupilot_result.get('parameters') == expected_params)
            
            row['ArduPilot_Result'] = json.dumps(ardupilot_result) if ardupilot_result else 'FAIL'
            row['ArduPilot_Correct'] = 'YES' if ardupilot_correct else 'NO'
            row['ArduPilot_Time'] = f"{ardupilot_time:.3f}"
            stats['ardupilot']['total'] += 1
            stats['ardupilot']['total_time'] += ardupilot_time
            if ardupilot_correct:
                stats['ardupilot']['correct'] += 1
                print(f"  ArduPilot: ✅ ({ardupilot_time:.2f}s)")
            else:
                print(f"  ArduPilot: ❌ ({ardupilot_time:.2f}s)")
            
            writer.writerow(row)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST COMPLETE - SUMMARY")
    print("="*80)
    
    for model_name, model_stats in [('Qwen 2.5 (3B)', stats['qwen25']),
                                     ('Gemma 3 (4B)', stats['gemma3']),
                                     ('ArduPilot Stage 1 (270M)', stats['ardupilot'])]:
        accuracy = (model_stats['correct'] / model_stats['total'] * 100) if model_stats['total'] > 0 else 0
        avg_time = model_stats['total_time'] / model_stats['total'] if model_stats['total'] > 0 else 0
        
        print(f"\n{model_name}:")
        print(f"  Accuracy: {accuracy:.1f}% ({model_stats['correct']}/{model_stats['total']})")
        print(f"  Avg Time: {avg_time:.3f}s")
        print(f"  Total Time: {model_stats['total_time']:.2f}s")
    
    print(f"\n{'='*80}")
    print(f"Detailed results saved to: {csv_filename}")
    print(f"{'='*80}")
    
    return csv_filename, stats


if __name__ == "__main__":
    csv_file, stats = run_comprehensive_test()
    
    print(f"\n✅ Test complete! Check {csv_file} for detailed results.")
