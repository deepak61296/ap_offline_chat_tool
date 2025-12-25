#!/usr/bin/env python3
"""
Comprehensive test suite for ArduPilot AI Assistant
Tests all 8 Stage 1 functions in demo mode
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.function_gemma import FunctionGemmaInterface
from examples.demo import MockDroneController


class TestSuite:
    """Comprehensive test suite for Stage 1 functions"""
    
    def __init__(self):
        self.gemma = FunctionGemmaInterface()
        self.drone = MockDroneController()
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test_function_parsing(self):
        """Test that FunctionGemma correctly parses function calls"""
        print("\n" + "="*60)
        print("TEST: Function Call Parsing")
        print("="*60)
        
        test_cases = [
            {
                "input": "<start_function_call>call:arm{}<end_function_call>",
                "expected_name": "arm",
                "expected_args": {}
            },
            {
                "input": "<start_function_call>call:takeoff{altitude:15}<end_function_call>",
                "expected_name": "takeoff",
                "expected_args": {"altitude": 15}
            },
            {
                "input": "<start_function_call>call:change_mode{mode:\"GUIDED\"}<end_function_call>",
                "expected_name": "change_mode",
                "expected_args": {"mode": "GUIDED"}
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            result = self.gemma.parse_function_call(test["input"])
            
            if result and result["function_name"] == test["expected_name"]:
                print(f"✅ Test {i}: Parsed '{test['expected_name']}' correctly")
                self.passed += 1
            else:
                print(f"❌ Test {i}: Failed to parse '{test['expected_name']}'")
                self.failed += 1
    
    def test_arm_function(self):
        """Test arm function"""
        print("\n" + "="*60)
        print("TEST: arm() Function")
        print("="*60)
        
        result = self.drone.arm()
        
        if result.get("status") == "success":
            print(f"✅ arm() executed successfully")
            print(f"   Message: {result.get('message')}")
            self.passed += 1
        else:
            print(f"❌ arm() failed: {result.get('message')}")
            self.failed += 1
    
    def test_disarm_function(self):
        """Test disarm function"""
        print("\n" + "="*60)
        print("TEST: disarm() Function")
        print("="*60)
        
        result = self.drone.disarm()
        
        if result.get("status") == "success":
            print(f"✅ disarm() executed successfully")
            print(f"   Message: {result.get('message')}")
            self.passed += 1
        else:
            print(f"❌ disarm() failed: {result.get('message')}")
            self.failed += 1
    
    def test_takeoff_function(self):
        """Test takeoff function"""
        print("\n" + "="*60)
        print("TEST: takeoff(altitude) Function")
        print("="*60)
        
        # First arm the drone
        self.drone.arm()
        
        # Test takeoff
        result = self.drone.takeoff(15)
        
        if result.get("status") == "success" and result.get("altitude") == 15:
            print(f"✅ takeoff(15) executed successfully")
            print(f"   Message: {result.get('message')}")
            self.passed += 1
        else:
            print(f"❌ takeoff(15) failed: {result.get('message')}")
            self.failed += 1
        
        # Test takeoff without arming
        self.drone.disarm()
        result = self.drone.takeoff(10)
        
        if result.get("status") == "error":
            print(f"✅ takeoff() correctly fails when not armed")
            self.passed += 1
        else:
            print(f"❌ takeoff() should fail when not armed")
            self.failed += 1
    
    def test_land_function(self):
        """Test land function"""
        print("\n" + "="*60)
        print("TEST: land() Function")
        print("="*60)
        
        result = self.drone.land()
        
        if result.get("status") == "success":
            print(f"✅ land() executed successfully")
            print(f"   Message: {result.get('message')}")
            self.passed += 1
        else:
            print(f"❌ land() failed: {result.get('message')}")
            self.failed += 1
    
    def test_rtl_function(self):
        """Test RTL function"""
        print("\n" + "="*60)
        print("TEST: rtl() Function")
        print("="*60)
        
        result = self.drone.rtl()
        
        if result.get("status") == "success":
            print(f"✅ rtl() executed successfully")
            print(f"   Message: {result.get('message')}")
            self.passed += 1
        else:
            print(f"❌ rtl() failed: {result.get('message')}")
            self.failed += 1
    
    def test_change_mode_function(self):
        """Test change_mode function"""
        print("\n" + "="*60)
        print("TEST: change_mode(mode) Function")
        print("="*60)
        
        test_modes = ["GUIDED", "LOITER", "RTL", "LAND"]
        
        for mode in test_modes:
            result = self.drone.change_mode(mode)
            
            if result.get("status") == "success":
                print(f"✅ change_mode('{mode}') executed successfully")
                self.passed += 1
            else:
                print(f"❌ change_mode('{mode}') failed")
                self.failed += 1
    
    def test_get_battery_function(self):
        """Test get_battery function"""
        print("\n" + "="*60)
        print("TEST: get_battery() Function")
        print("="*60)
        
        result = self.drone.get_battery()
        
        if (result.get("status") == "success" and 
            "voltage" in result and 
            "current" in result and 
            "remaining" in result):
            print(f"✅ get_battery() executed successfully")
            print(f"   Voltage: {result['voltage']}V")
            print(f"   Current: {result['current']}A")
            print(f"   Remaining: {result['remaining']}%")
            
            # Test formatting
            formatted = self.gemma.format_result_message("get_battery", result)
            print(f"   Formatted: {formatted}")
            
            if "🔋" in formatted and str(result['voltage']) in formatted:
                print(f"✅ Battery formatting correct")
                self.passed += 2  # +1 for function, +1 for formatting
            else:
                print(f"❌ Battery formatting incorrect")
                self.passed += 1
                self.failed += 1
        else:
            print(f"❌ get_battery() failed or missing data")
            self.failed += 1
    
    def test_get_position_function(self):
        """Test get_position function"""
        print("\n" + "="*60)
        print("TEST: get_position() Function")
        print("="*60)
        
        result = self.drone.get_position()
        
        if (result.get("status") == "success" and 
            "latitude" in result and 
            "longitude" in result and 
            "altitude" in result):
            print(f"✅ get_position() executed successfully")
            print(f"   Latitude: {result['latitude']}°")
            print(f"   Longitude: {result['longitude']}°")
            print(f"   Altitude: {result['altitude']}m")
            print(f"   Heading: {result.get('heading', 0)}°")
            
            # Test formatting
            formatted = self.gemma.format_result_message("get_position", result)
            print(f"   Formatted: {formatted}")
            
            if "📍" in formatted and str(result['latitude']) in formatted:
                print(f"✅ Position formatting correct")
                self.passed += 2  # +1 for function, +1 for formatting
            else:
                print(f"❌ Position formatting incorrect")
                self.passed += 1
                self.failed += 1
        else:
            print(f"❌ get_position() failed or missing data")
            self.failed += 1
    
    def test_result_formatting(self):
        """Test result message formatting for all function types"""
        print("\n" + "="*60)
        print("TEST: Result Message Formatting")
        print("="*60)
        
        test_cases = [
            {
                "function": "arm",
                "result": {"status": "success", "message": "Drone armed"},
                "should_contain": "Drone armed"
            },
            {
                "function": "get_mode",
                "result": {"status": "success", "mode": "GUIDED"},
                "should_contain": "GUIDED"
            },
            {
                "function": "is_armable",
                "result": {"status": "success", "armable": True},
                "should_contain": "ready to arm"
            }
        ]
        
        for test in test_cases:
            formatted = self.gemma.format_result_message(test["function"], test["result"])
            
            if test["should_contain"] in formatted:
                print(f"✅ {test['function']} formatting correct: {formatted}")
                self.passed += 1
            else:
                print(f"❌ {test['function']} formatting incorrect: {formatted}")
                self.failed += 1
    
    def run_all_tests(self):
        """Run all tests and print summary"""
        print("\n" + "="*60)
        print("ARDUPILOT AI ASSISTANT - TEST SUITE")
        print("Stage 1 Functions - Demo Mode")
        print("="*60)
        
        # Run all tests
        self.test_function_parsing()
        self.test_arm_function()
        self.test_disarm_function()
        self.test_takeoff_function()
        self.test_land_function()
        self.test_rtl_function()
        self.test_change_mode_function()
        self.test_get_battery_function()
        self.test_get_position_function()
        self.test_result_formatting()
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {percentage:.1f}%")
        print("="*60)
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED! 🎉\n")
            return 0
        else:
            print(f"\n⚠️  {self.failed} TEST(S) FAILED ⚠️\n")
            return 1


if __name__ == "__main__":
    suite = TestSuite()
    exit_code = suite.run_all_tests()
    sys.exit(exit_code)
