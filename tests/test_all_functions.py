"""
Comprehensive Automated Test Suite for ArduPilot AI Backend
Tests all command extraction, AI responses, and function availability
Generates detailed HTML report
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Configuration
BACKEND_URL = "http://localhost:5000"
TIMEOUT = 30

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestResult:
    def __init__(self, category: str, test_name: str, input_text: str, 
                 expected_command: str, actual_response: str, 
                 extracted_command: Dict, passed: bool, error: str = None):
        self.category = category
        self.test_name = test_name
        self.input_text = input_text
        self.expected_command = expected_command
        self.actual_response = actual_response
        self.extracted_command = extracted_command
        self.passed = passed
        self.error = error
        self.timestamp = datetime.now()

class AIBackendTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        
    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    def print_test(self, test_name: str, passed: bool, details: str = ""):
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"  {status} - {test_name}")
        if details and not passed:
            print(f"    {Colors.YELLOW}→ {details}{Colors.RESET}")
    
    def check_backend_health(self) -> bool:
        """Check if backend is running and healthy"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
        except:
            return False
        return False
    
    def send_message(self, message: str, mode: str = "agent", model: str = "qwen2.5:3b") -> Tuple[str, Dict]:
        """Send message to backend and get response + extracted command"""
        try:
            payload = {
                "message": message,
                "mode": mode,
                "model": model,
                "telemetry": {
                    "battery": {"voltage": 12.6, "current": 5.2, "remaining": 85},
                    "gps": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 50, "satellites": 12, "fix_type": "3D Fix"},
                    "attitude": {"roll": 0, "pitch": 0, "yaw": 90},
                    "speed": {"ground_speed": 0, "air_speed": 0, "climb_rate": 0},
                    "status": {"mode": "GUIDED", "armed": True}
                }
            }
            
            response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", ""), data.get("command", {})
            else:
                # Return actual error text instead of just status code
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text[:200])
                except:
                    error_msg = response.text[:200]
                return f"Error {response.status_code}: {error_msg}", {}
        except requests.exceptions.Timeout:
            return "Error: Request timed out", {}
        except Exception as e:
            return f"Exception: {str(e)}", {}
    
    def test_command(self, category: str, test_name: str, input_text: str, 
                     expected_command_type: str, expected_phrase: str = None) -> bool:
        """Test a single command"""
        response, command = self.send_message(input_text, mode="agent")
        
        # Check if command was extracted
        command_type = command.get("type") if command else None
        passed = command_type == expected_command_type
        
        # If expected phrase is provided, check response contains it
        if expected_phrase and passed:
            passed = expected_phrase.lower() in response.lower()
        
        # Create error message with actual response for debugging
        error_msg = None
        if not passed:
            if command_type != expected_command_type:
                error_msg = f"Expected: {expected_command_type}, Got: {command_type}"
                # Add actual response for debugging
                error_msg += f"\n    AI Response: '{response[:100]}...'"
            elif expected_phrase:
                error_msg = f"Response missing phrase: '{expected_phrase}'"
                error_msg += f"\n    AI Response: '{response[:100]}...'"
        
        result = TestResult(
            category=category,
            test_name=test_name,
            input_text=input_text,
            expected_command=expected_command_type,
            actual_response=response,
            extracted_command=command,
            passed=passed,
            error=error_msg
        )
        
        self.results.append(result)
        self.print_test(test_name, passed, result.error)
        
        # Add small delay to avoid overwhelming the backend
        time.sleep(0.5)
        
        return passed
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        self.start_time = datetime.now()
        
        print(f"\n{Colors.BOLD}ArduPilot AI Backend - Comprehensive Test Suite{Colors.RESET}")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Check backend health
        self.print_header("1. Backend Health Check")
        if not self.check_backend_health():
            print(f"{Colors.RED}✗ Backend is not running or unhealthy!{Colors.RESET}")
            print(f"{Colors.YELLOW}Please start the backend with: scripts\\start_backend.bat{Colors.RESET}")
            return False
        print(f"{Colors.GREEN}✓ Backend is healthy and running{Colors.RESET}")
        
        # Diagnostic test - show what AI actually responds with
        self.print_header("2. Diagnostic Test - Sample Responses")
        print(f"{Colors.YELLOW}Testing a few commands to see actual AI responses...{Colors.RESET}\n")
        
        test_inputs = [
            "arm the drone",
            "takeoff to 15 meters", 
            "move north 20 meters"
        ]
        
        for test_input in test_inputs:
            response, command = self.send_message(test_input, mode="agent")
            cmd_type = command.get("type") if command else "None"
            print(f"  Input: '{test_input}'")
            print(f"  Response: '{response[:150]}...'")
            print(f"  Extracted: {cmd_type}")
            print()
        
        # Test 1: Basic Flight Commands
        self.print_header("3. Basic Flight Commands (5 tests)")
        self.test_command("Flight", "ARM command", "arm the drone", "ARM", "arming the drone")
        self.test_command("Flight", "DISARM command", "disarm", "DISARM", "disarming")
        self.test_command("Flight", "TAKEOFF command", "takeoff to 15 meters", "TAKEOFF", "taking off to 15")
        self.test_command("Flight", "LAND command", "land the drone", "LAND", "landing")
        self.test_command("Flight", "RTL command", "return to launch", "RTL", "returning to launch")
        
        # Test 2: Movement Commands
        self.print_header("4. Directional Movement Commands (8 tests)")
        self.test_command("Movement", "Move North", "move north 20 meters", "MOVE_DIRECTION", "moving north 20")
        self.test_command("Movement", "Move South", "move south 30m", "MOVE_DIRECTION", "moving south 30")
        self.test_command("Movement", "Move East", "move east 50 meters", "MOVE_DIRECTION", "moving east 50")
        self.test_command("Movement", "Move West", "move west 10m", "MOVE_DIRECTION", "moving west 10")
        self.test_command("Movement", "Go North variant", "go north 25 meters", "MOVE_DIRECTION")
        self.test_command("Movement", "Fly East variant", "fly east 40m", "MOVE_DIRECTION")
        self.test_command("Movement", "Move South variant", "move 35 meters south", "MOVE_DIRECTION")
        self.test_command("Movement", "Move West variant", "go 15m west", "MOVE_DIRECTION")
        
        # Test 3: Altitude Commands
        self.print_header("5. Altitude Change Commands (8 tests)")
        self.test_command("Altitude", "Increase altitude", "increase altitude by 20m", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Decrease altitude", "decrease altitude by 10m", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Go up", "go up 15 meters", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Go down", "go down 5 meters", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Ascend", "ascend 25m", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Descend", "descend 8 meters", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Climb", "climb 12m", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Drop", "drop 6 meters", "ALTITUDE_CHANGE")
        
        # Test 4: Mode Changes
        self.print_header("6. Mode Change Commands (6 tests)")
        self.test_command("Mode", "Change to GUIDED", "change mode to guided", "CHANGE_MODE", "changing mode to guided")
        self.test_command("Mode", "Switch to AUTO", "switch to auto", "CHANGE_MODE", "changing mode to auto")
        self.test_command("Mode", "Change to LOITER", "change mode to loiter", "CHANGE_MODE")
        self.test_command("Mode", "Switch to STABILIZE", "switch to stabilize", "CHANGE_MODE")
        self.test_command("Mode", "Change to ALT_HOLD", "change mode to alt_hold", "CHANGE_MODE")
        self.test_command("Mode", "Switch to LAND", "switch flight mode to land", "CHANGE_MODE")
        
        # Test 5: Navigation Commands
        self.print_header("7. Navigation Commands (5 tests)")
        self.test_command("Navigation", "GOTO coordinates", "fly to coordinates 37.7749, -122.4194", "GOTO")
        self.test_command("Navigation", "GOTO with altitude", "fly to 37.7749, -122.4194 at 100 meters", "GOTO")
        self.test_command("Navigation", "GOTO home", "fly to home", "GOTO_HOME")
        self.test_command("Navigation", "Return home", "go to home position", "GOTO_HOME")
        self.test_command("Navigation", "Navigate to coords", "navigate to 40.7128, -74.0060", "GOTO")
        
        # Test 6: Parameter Commands
        self.print_header("8. Parameter Commands (6 tests)")
        self.test_command("Parameters", "GET parameter", "what is parameter WPNAV_SPEED?", "GET_PARAM")
        self.test_command("Parameters", "SET parameter", "set parameter DISARM_DELAY to 40", "SET_PARAM")
        self.test_command("Parameters", "GET BATT_CAPACITY", "get parameter BATT_CAPACITY", "GET_PARAM")
        self.test_command("Parameters", "SET WPNAV_SPEED", "set WPNAV_SPEED to 500", "SET_PARAM")
        self.test_command("Parameters", "Check parameter", "check parameter FENCE_ENABLE", "GET_PARAM")
        self.test_command("Parameters", "Update parameter", "update parameter RTL_ALT to 50", "SET_PARAM")
        
        # Test 7: System Commands
        self.print_header("9. System Commands (3 tests)")
        self.test_command("System", "REBOOT", "reboot the flight controller", "REBOOT")
        self.test_command("System", "RESTART", "restart the system", "REBOOT")
        self.test_command("System", "Reboot FC", "reboot flight controller", "REBOOT")
        
        # Test 8: Conversational (No Command)
        self.print_header("10. Conversational Queries (No Commands) (10 tests)")
        response, cmd = self.send_message("hello", "agent")
        self.results.append(TestResult("Conversational", "Greeting", "hello", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Greeting response", cmd is None or not cmd)
        
        response, cmd = self.send_message("what can you do?", "agent")
        self.results.append(TestResult("Conversational", "Capabilities", "what can you do?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Capabilities list", cmd is None or not cmd)
        
        response, cmd = self.send_message("what is my current altitude?", "agent")
        self.results.append(TestResult("Conversational", "Altitude query", "what is my current altitude?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Altitude query (no command)", cmd is None or not cmd)
        
        response, cmd = self.send_message("what's the battery level?", "agent")
        self.results.append(TestResult("Conversational", "Battery query", "what's the battery level?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Battery query (no command)", cmd is None or not cmd)
        
        response, cmd = self.send_message("am I armed?", "agent")
        self.results.append(TestResult("Conversational", "Armed status", "am I armed?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Armed status query (no command)", cmd is None or not cmd)
        
        response, cmd = self.send_message("where am I?", "ask")
        has_coords = "37.7749" in response or "latitude" in response.lower()
        self.results.append(TestResult("Conversational", "Location query (Ask mode)", "where am I?", "GPS coords", response, cmd, has_coords))
        self.print_test("Location query returns GPS", has_coords)
        
        response, cmd = self.send_message("what mode am I in?", "agent")
        self.results.append(TestResult("Conversational", "Mode query", "what mode am I in?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Mode query (no command)", cmd is None or not cmd)
        
        response, cmd = self.send_message("do I have GPS lock?", "agent")
        self.results.append(TestResult("Conversational", "GPS query", "do I have GPS lock?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("GPS query (no command)", cmd is None or not cmd)
        
        response, cmd = self.send_message("how are you?", "agent")
        self.results.append(TestResult("Conversational", "How are you", "how are you?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("How are you (no command)", cmd is None or not cmd)
        
        response, cmd = self.send_message("tell me about yourself", "agent")
        self.results.append(TestResult("Conversational", "About query", "tell me about yourself", "None", response, cmd, cmd is None or not cmd))
        self.print_test("About query (no command)", cmd is None or not cmd)
        
        # Test 9: Edge Cases
        self.print_header("11. Edge Cases & Safety (8 tests)")
        self.test_command("Edge Cases", "Excessive altitude", "takeoff to 500 meters", "ERROR")
        self.test_command("Edge Cases", "Excessive distance", "move north 5000 meters", "ERROR")
        self.test_command("Edge Cases", "Invalid mode", "change mode to INVALID_MODE", "ERROR")
        self.test_command("Edge Cases", "Invalid coordinates", "fly to 200, 300", "ERROR")
        
        response, cmd = self.send_message("maybe arm the drone?", "agent")
        self.results.append(TestResult("Edge Cases", "Uncertain command", "maybe arm?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Uncertain command (should not execute)", cmd is None or not cmd)
        
        response, cmd = self.send_message("can you arm?", "agent")
        self.results.append(TestResult("Edge Cases", "Question not command", "can you arm?", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Question not command (should not execute)", cmd is None or not cmd)
        
        response, cmd = self.send_message("I want to takeoff", "agent")
        self.results.append(TestResult("Edge Cases", "Indirect request", "I want to takeoff", "None", response, cmd, cmd is None or not cmd))
        self.print_test("Indirect request (should not execute)", cmd is None or not cmd)
        
        response, cmd = self.send_message("arm", "ask")
        has_warning = "ask mode" in response.lower() or "agent mode" in response.lower()
        self.results.append(TestResult("Edge Cases", "Command in Ask mode", "arm (in Ask mode)", "Rejected", response, cmd, has_warning))
        self.print_test("Command rejected in Ask mode", has_warning)
        
        self.end_time = datetime.now()
        
        return True
    
    def generate_report(self):
        """Generate HTML report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Print summary to console
        self.print_header("Test Summary")
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds\n")
        
        # Generate HTML report
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ArduPilot AI Backend Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 48px; font-weight: bold; }}
        .stat-label {{ color: #666; margin-top: 10px; }}
        .pass {{ color: #27ae60; }}
        .fail {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .category {{ background: #ecf0f1; font-weight: bold; }}
        .pass-badge {{ background: #27ae60; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px; }}
        .fail-badge {{ background: #e74c3c; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px; }}
        .error {{ color: #e74c3c; font-size: 12px; }}
        .response {{ font-size: 12px; color: #666; max-width: 400px; overflow: hidden; text-overflow: ellipsis; }}
        .command {{ font-family: monospace; background: #ecf0f1; padding: 2px 6px; border-radius: 3px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚁 ArduPilot AI Backend - Comprehensive Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Duration: {duration:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat">
                <div class="stat-value pass">{passed}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat">
                <div class="stat-value fail">{failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {'#27ae60' if success_rate >= 90 else '#e67e22' if success_rate >= 70 else '#e74c3c'}">{success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Test Name</th>
                <th>Input</th>
                <th>Expected</th>
                <th>Extracted Command</th>
                <th>AI Response</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
"""
        
        current_category = None
        for result in self.results:
            if current_category != result.category:
                html += f'<tr class="category"><td colspan="7">{result.category}</td></tr>\n'
                current_category = result.category
            
            status_badge = '<span class="pass-badge">✓ PASS</span>' if result.passed else '<span class="fail-badge">✗ FAIL</span>'
            cmd_type = result.extracted_command.get('type', 'None') if result.extracted_command else 'None'
            cmd_display = f'<span class="command">{cmd_type}</span>'
            
            html += f"""<tr>
                <td></td>
                <td>{result.test_name}</td>
                <td><em>{result.input_text}</em></td>
                <td><span class="command">{result.expected_command}</span></td>
                <td>{cmd_display}</td>
                <td class="response">{result.actual_response[:100]}...</td>
                <td>{status_badge}</td>
            </tr>\n"""
            
            if result.error:
                html += f'<tr><td colspan="7" class="error">→ {result.error}</td></tr>\n'
        
        html += """
        </tbody>
    </table>
</body>
</html>
"""
        
        # Save report
        report_path = "test_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"{Colors.GREEN}✓ HTML report generated: {report_path}{Colors.RESET}")
        print(f"{Colors.YELLOW}Open {report_path} in your browser to view detailed results{Colors.RESET}\n")
        
        return report_path

def main():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}ArduPilot AI Backend - Comprehensive Automated Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    tester = AIBackendTester()
    
    if not tester.run_all_tests():
        print(f"\n{Colors.RED}Tests aborted - backend not available{Colors.RESET}\n")
        sys.exit(1)
    
    tester.generate_report()
    
    # Final summary
    total = len(tester.results)
    passed = sum(1 for r in tester.results if r.passed)
    failed = total - passed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    if success_rate >= 90:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 EXCELLENT! All systems operational!{Colors.RESET}\n")
    elif success_rate >= 70:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  GOOD, but some issues need attention{Colors.RESET}\n")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ CRITICAL ISSUES DETECTED{Colors.RESET}\n")

if __name__ == "__main__":
    main()
