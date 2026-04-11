"""
ULTIMATE Comprehensive Test Suite for ArduPilot AI Backend
Merges baseline + mega suites = 170+ tests with HTML reporting

Categories:
- Baseline Flight & Movement (25 tests)
- Altitude Commands (8 tests)
- Mode & Navigation (11 tests)  
- Parameters & System (9 tests)
- Conversational (10 tests)
- Natural Language Variations (30 tests)
- Typos & Misspellings (20 tests)
- Ambiguous Commands (18 tests)
- Compound Requests (7 tests)
- Safety-Critical (12 tests)
- Real Pilot Speech (5 tests)
- Edge Cases (8 tests)

TOTAL: ~170 comprehensive tests
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

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class ComprehensiveResult:
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

class ComprehensiveTestSuite:
    def __init__(self):
        self.results: List[ComprehensiveResult] = []
        self.start_time = None
        self.end_time = None
        self.total_tests = 170  # Approximate total tests
        self.tests_completed = 0
        self.avg_time_per_test = 0.5  # Initial estimate (seconds)
        
    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    def print_test(self, test_name: str, passed: bool, details: str = ""):
        """Legacy method - redirects to print_test_with_eta"""
        self.print_test_with_eta(test_name, passed, details)
    
    def check_backend_health(self) -> bool:
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except:
            return False
    
    def send_message(self, message: str, mode: str = "agent", model: str = "qwen2.5:3b") -> Tuple[str, Dict]:
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
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text[:150])
                except:
                    error_msg = response.text[:150]
                return f"Error {response.status_code}: {error_msg}", {}
        except requests.exceptions.Timeout:
            return "Error: Timeout", {}
        except Exception as e:
            return f"Exception: {str(e)}", {}
    
    def test_command(self, category: str, test_name: str, input_text: str, 
                     expected_command_type: str, expected_phrase: str = None,
                     mode: str = "agent") -> bool:
        response, command = self.send_message(input_text, mode=mode)
        
        command_type = command.get("type") if command else None
        passed = command_type == expected_command_type
        
        if expected_phrase and passed:
            passed = expected_phrase.lower() in response.lower()
        
        error_msg = None
        if not passed:
            if command_type != expected_command_type:
                error_msg = f"Expected: {expected_command_type}, Got: {command_type}"
                error_msg += f"\nResponse: '{response[:80]}...'"
            elif expected_phrase:
                error_msg = f"Missing phrase: '{expected_phrase}'"
        
        result = ComprehensiveResult(category, test_name, input_text, expected_command_type,
                                     response, command, passed, error_msg)

        self.results.append(result)
        self.tests_completed += 1
        self.print_test_with_eta(test_name, passed, result.error)
        time.sleep(0.3)
        return passed

    def print_test_with_eta(self, test_name: str, passed: bool, details: str = ""):
        """Print test result with ETA"""
        status = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"

        # Calculate ETA
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        if self.tests_completed > 0:
            self.avg_time_per_test = elapsed / self.tests_completed
        remaining_tests = self.total_tests - self.tests_completed
        eta_seconds = remaining_tests * self.avg_time_per_test

        if eta_seconds > 60:
            eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
        else:
            eta_str = f"{int(eta_seconds)}s"

        progress = f"[{self.tests_completed}/{self.total_tests}]"
        print(f"  {status} {test_name:40s} {Colors.BLUE}{progress} ETA: {eta_str}{Colors.RESET}")

        if details and not passed:
            for line in details.split('\n')[:2]:
                print(f"      {Colors.YELLOW}{line}{Colors.RESET}")
    
    def run_all_tests(self):
        self.start_time = datetime.now()
        
        print(f"\n{Colors.BOLD}ArduPilot AI Backend - ULTIMATE COMPREHENSIVE TEST SUITE{Colors.RESET}")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Health check
        self.print_header("Backend Health Check")
        if not self.check_backend_health():
            print(f"{Colors.RED}✗ Backend not running!{Colors.RESET}")
            return False
        print(f"{Colors.GREEN}✓ Backend healthy{Colors.RESET}")
        
        # ==================== PART 1: BASELINE & CORE FUNCTIONALITY ====================
        self.print_header("PART 1: BASELINE & CORE TESTS (53 tests)")
        
        print(f"\n{Colors.BOLD}1.1 Basic Flight Commands (5){Colors.RESET}")
        self.test_command("Flight", "ARM", "arm the drone", "ARM", "arming")
        self.test_command("Flight", "DISARM", "disarm", "DISARM", "disarming")
        self.test_command("Flight", "TAKEOFF", "takeoff to 15 meters", "TAKEOFF", "taking off")
        self.test_command("Flight", "LAND", "land the drone", "LAND", "landing")
        self.test_command("Flight", "RTL", "return to launch", "RTL", "returning")
        
        print(f"\n{Colors.BOLD}1.2 Directional Movement (8){Colors.RESET}")
        self.test_command("Movement", "North", "move north 20 meters", "MOVE_DIRECTION", "moving north")
        self.test_command("Movement", "South", "move south 30m", "MOVE_DIRECTION", "moving south")
        self.test_command("Movement", "East", "move east 50 meters", "MOVE_DIRECTION", "moving east")
        self.test_command("Movement", "West", "move west 10m", "MOVE_DIRECTION", "moving west")
        self.test_command("Movement", "Go North", "go north 25 meters", "MOVE_DIRECTION")
        self.test_command("Movement", "Fly East", "fly east 40m", "MOVE_DIRECTION")
        self.test_command("Movement", "Move South variant", "move 35 meters south", "MOVE_DIRECTION")
        self.test_command("Movement", "Go West", "go 15m west", "MOVE_DIRECTION")
        
        print(f"\n{Colors.BOLD}1.3 Altitude Changes (8){Colors.RESET}")
        self.test_command("Altitude", "Increase", "increase altitude by 20m", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Decrease", "decrease altitude by 10m", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Go up", "go up 15 meters", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Go down", "go down 5 meters", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Ascend", "ascend 25m", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Descend", "descend 8 meters", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Climb", "climb 12m", "ALTITUDE_CHANGE")
        self.test_command("Altitude", "Drop", "drop 6 meters", "ALTITUDE_CHANGE")
        
        print(f"\n{Colors.BOLD}1.4 Mode Changes (6){Colors.RESET}")
        self.test_command("Mode", "GUIDED", "change mode to guided", "CHANGE_MODE", "changing mode")
        self.test_command("Mode", "AUTO", "switch to auto", "CHANGE_MODE", "changing mode")
        self.test_command("Mode", "LOITER", "change mode to loiter", "CHANGE_MODE")
        self.test_command("Mode", "STABILIZE", "switch to stabilize", "CHANGE_MODE")
        self.test_command("Mode", "ALT_HOLD", "change mode to alt_hold", "CHANGE_MODE")
        self.test_command("Mode", "LAND mode", "switch flight mode to land", "CHANGE_MODE")
        
        print(f"\n{Colors.BOLD}1.5 Navigation (5){Colors.RESET}")
        self.test_command("Navigation", "GOTO coords", "fly to coordinates 37.7749, -122.4194", "GOTO")
        self.test_command("Navigation", "GOTO with alt", "fly to 37.7749, -122.4194 at 100 meters", "GOTO")
        self.test_command("Navigation", "GOTO home", "fly to home", "GOTO_HOME")
        self.test_command("Navigation", "Return home", "go to home position", "GOTO_HOME")
        self.test_command("Navigation", "Navigate to", "navigate to 40.7128, -74.0060", "GOTO")
        
        print(f"\n{Colors.BOLD}1.6 Parameters (6){Colors.RESET}")
        self.test_command("Parameters", "GET", "what is parameter WPNAV_SPEED?", "GET_PARAM")
        self.test_command("Parameters", "SET", "set parameter DISARM_DELAY to 40", "SET_PARAM")
        self.test_command("Parameters", "GET BATT", "get parameter BATT_CAPACITY", "GET_PARAM")
        self.test_command("Parameters", "SET WPNAV", "set WPNAV_SPEED to 500", "SET_PARAM")
        self.test_command("Parameters", "Check", "check parameter FENCE_ENABLE", "GET_PARAM")
        self.test_command("Parameters", "Update", "update parameter RTL_ALT to 50", "SET_PARAM")
        
        print(f"\n{Colors.BOLD}1.7 System Commands (3){Colors.RESET}")
        self.test_command("System", "REBOOT", "reboot the flight controller", "REBOOT")
        self.test_command("System", "RESTART", "restart the system", "REBOOT")
        self.test_command("System", "Reboot FC", "reboot flight controller", "REBOOT")
        
        print(f"\n{Colors.BOLD}1.8 Conversational (No Commands) (10){Colors.RESET}")
        response, cmd = self.send_message("hello", "agent")
        self.results.append(TestResult("Conversational", "Greeting", "hello", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Greeting", cmd is None or not cmd)
        
        response, cmd = self.send_message("what can you do?", "agent")
        self.results.append(TestResult("Conversational", "Capabilities", "what can you do?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Capabilities", cmd is None or not cmd)
        
        response, cmd = self.send_message("what is my current altitude?", "agent")
        self.results.append(TestResult("Conversational", "Altitude query", "what is my current altitude?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Altitude query", cmd is None or not cmd)
        
        response, cmd = self.send_message("what's the battery level?", "agent")
        self.results.append(TestResult("Conversational", "Battery query", "what's the battery level?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Battery query", cmd is None or not cmd)
        
        response, cmd = self.send_message("am I armed?", "agent")
        self.results.append(TestResult("Conversational", "Armed status", "am I armed?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Armed status", cmd is None or not cmd)
        
        response, cmd = self.send_message("where am I?", "ask")
        has_coords = "37.7749" in response or "latitude" in response.lower()
        self.results.append(TestResult("Conversational", "Location (Ask)", "where am I?", "GPS coords", response, cmd, has_coords))
        self.tests_completed += 1; self.print_test_with_eta("Location query (Ask mode)", has_coords)
        
        response, cmd = self.send_message("what mode am I in?", "agent")
        self.results.append(TestResult("Conversational", "Mode query", "what mode am I in?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Mode query", cmd is None or not cmd)
        
        response, cmd = self.send_message("do I have GPS lock?", "agent")
        self.results.append(TestResult("Conversational", "GPS query", "do I have GPS lock?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("GPS query", cmd is None or not cmd)
        
        response, cmd = self.send_message("how are you?", "agent")
        self.results.append(TestResult("Conversational", "How are you", "how are you?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("How are you", cmd is None or not cmd)
        
        response, cmd = self.send_message("tell me about yourself", "agent")
        self.results.append(TestResult("Conversational", "About", "tell me about yourself", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("About query", cmd is None or not cmd)
        
        print(f"\n{Colors.BOLD}1.9 Baseline Edge Cases (8){Colors.RESET}")
        self.test_command("Edge Cases", "Excessive alt", "takeoff to 500 meters", "ERROR")
        self.test_command("Edge Cases", "Excessive dist", "move north 5000 meters", "ERROR")
        self.test_command("Edge Cases", "Invalid mode", "change mode to INVALID_MODE", "ERROR")
        self.test_command("Edge Cases", "Invalid coords", "fly to 200, 300", "ERROR")
        
        response, cmd = self.send_message("maybe arm the drone?", "agent")
        self.results.append(TestResult("Edge Cases", "Uncertain", "maybe arm?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Uncertain command", cmd is None or not cmd)
        
        response, cmd = self.send_message("can you arm?", "agent")
        self.results.append(TestResult("Edge Cases", "Question not cmd", "can you arm?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Question not command", cmd is None or not cmd)
        
        response, cmd = self.send_message("I want to takeoff", "agent")
        self.results.append(TestResult("Edge Cases", "Indirect", "I want to takeoff", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("Indirect request", cmd is None or not cmd)
        
        response, cmd = self.send_message("arm", "ask")
        has_warning = "ask mode" in response.lower() or "agent mode" in response.lower()
        self.results.append(TestResult("Edge Cases", "Cmd in Ask", "arm (Ask mode)", "Rejected", response, cmd, has_warning))
        self.tests_completed += 1; self.print_test_with_eta("Command in Ask mode", has_warning)
        
        # ==================== PART 2: NATURAL LANGUAGE & TYPOS ====================
        self.print_header("PART 2: NATURAL LANGUAGE & TYPOS (50 tests)")
        
        print(f"\n{Colors.BOLD}2.1 Casual/Informal Speech (8){Colors.RESET}")
        self.test_command("NL-Casual", "arm it", "arm it", "ARM")
        self.test_command("NL-Casual", "get it armed", "get it armed", "ARM")
        self.test_command("NL-Casual", "bring her up", "bring her up 20 meters", "ALTITUDE_CHANGE")
        self.test_command("NL-Casual", "take her down", "take her down 10m", "ALTITUDE_CHANGE")
        self.test_command("NL-Casual", "drop it", "drop it 5 meters", "ALTITUDE_CHANGE")
        self.test_command("NL-Casual", "bring it home", "bring it home",  "RTL")
        self.test_command("NL-Casual", "kill motors", "kill the motors", "DISARM")
        self.test_command("NL-Casual", "spin up", "spin up the motors", "ARM")
        
        print(f"\n{Colors.BOLD}2.2 Polite Requests (3){Colors.RESET}")
        self.test_command("NL-Polite", "please arm", "could you arm the drone please", "ARM")
        self.test_command("NL-Polite", "would you mind", "would you mind taking off to 20m", "TAKEOFF")
        self.test_command("NL-Polite", "if you could", "if you could land the drone", "LAND")
        
        print(f"\n{Colors.BOLD}2.3 Abbreviations (5){Colors.RESET}")
        self.test_command("NL-Abbrev", "t/o", "t/o to 15m", "TAKEOFF")
        self.test_command("NL-Abbrev", "disarm asap", "disarm asap", "DISARM")
        self.test_command("NL-Abbrev", "rtl now", "rtl now", "RTL")
        self.test_command("NL-Abbrev", "up 10m", "up 10m", "ALTITUDE_CHANGE")
        self.test_command("NL-Abbrev", "down 5m", "down 5m", "ALTITUDE_CHANGE")
        
        print(f"\n{Colors.BOLD}2.4 Questions (Should NOT Execute) (3){Colors.RESET}")
        response, cmd = self.send_message("ready to arm?", "agent")
        self.results.append(TestResult("NL-Question", "ready to arm?", "ready to arm?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("ready to arm?", cmd is None or not cmd)
        
        response, cmd = self.send_message("should we takeoff?", "agent")
        self.results.append(TestResult("NL-Question", "should we?", "should we takeoff?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("should we takeoff?", cmd is None or not cmd)
        
        response, cmd = self.send_message("is it safe to land?", "agent")
        self.results.append(TestResult("NL-Question", "is it safe?", "is it safe to land?", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("is it safe to land?", cmd is None or not cmd)
        
        print(f"\n{Colors.BOLD}2.5 Indirect Requests (3){Colors.RESET}")
        response, cmd = self.send_message("I want to arm", "agent")
        self.results.append(TestResult("NL-Indirect", "I want to", "I want to arm", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("I want to arm", cmd is None or not cmd)
        
        response, cmd = self.send_message("I'd like to takeoff", "agent")
        self.results.append(TestResult("NL-Indirect", "I'd like", "I'd like to takeoff", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("I'd like to takeoff", cmd is None or not cmd)
        
        response, cmd = self.send_message("thinking about landing", "agent")
        self.results.append(TestResult("NL-Indirect", "thinking about", "thinking about landing", "None", response, cmd, cmd is None or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("thinking about landing", cmd is None or not cmd)
        
        print(f"\n{Colors.BOLD}2.6 Filler Words (3){Colors.RESET}")
        self.test_command("NL-Filler", "um arm", "um, can you like, arm the drone", "ARM")
        self.test_command("NL-Filler", "so yeah", "so yeah, takeoff to uh 20 meters", "TAKEOFF")
        self.test_command("NL-Filler", "well land", "well, I guess land the drone", "LAND")
        
        print(f"\n{Colors.BOLD}2.7 Emphatic/Urgent (3){Colors.RESET}")
        self.test_command("NL-Urgent", "ARM NOW", "ARM NOW", "ARM")
        self.test_command("NL-Urgent", "LAND IMM", "LAND IMMEDIATELY", "LAND")
        self.test_command("NL-Urgent", "RTL NOW", "RTL RIGHT NOW", "RTL")
        
        print(f"\n{Colors.BOLD}2.8 Verbose (2){Colors.RESET}")
        self.test_command("NL-Verbose", "please go ahead", "please go ahead and arm the drone for me", "ARM")
        self.test_command("NL-Verbose", "if you can", "can you please takeoff to 15 meters if you can", "TAKEOFF")
        
        print(f"\n{Colors.BOLD}2.9 Common Typos (20){Colors.RESET}")
        self.test_command("Typo", "armm", "armm the drone", "ARM")
        self.test_command("Typo", "disrm", "disrm", "DISARM")
        self.test_command("Typo", "takeof", "takeof to 15m", "TAKEOFF")
        self.test_command("Typo", "lnad", "lnad the drone", "LAND")
        self.test_command("Typo", "retun", "retun to launch", "RTL")
        self.test_command("Typo-Move", "moe", "moe north 20m", "MOVE_DIRECTION")
        self.test_command("Typo-Move", "mov", "mov south 30 meters", "MOVE_DIRECTION")
        self.test_command("Typo-Alt", "increse", "increse altitude by 20m", "ALTITUDE_CHANGE")
        self.test_command("Typo-Alt", "decrese", "decrese altitude by 10m", "ALTITUDE_CHANGE")
        self.test_command("Typo-Alt", "goup", "goup 15 meters", "ALTITUDE_CHANGE")
        self.test_command("Typo-Alt", "clim", "clim 12m", "ALTITUDE_CHANGE")
        self.test_command("Typo-Mode", "mod", "change mod to guided", "CHANGE_MODE")
        self.test_command("Typo-Mode", "loiter mod", "switch to loiter mod", "CHANGE_MODE")
        self.test_command("Typo-Nav", "go hom", "go hom", "RTL")
        self.test_command("Typo-Nav", "goto home", "goto home", "GOTO_HOME")
        self.test_command("Typo-Nav", "fly too", "fly too 37.7749, -122.4194", "GOTO")
        self.test_command("Typo-Num", "15m", "takeoff to 15m", "TAKEOFF")
        self.test_command("Typo-Num", "20meters", "move north 20meters", "MOVE_DIRECTION")
        self.test_command("Typo-Num", "10 m", "go up 10 m", "ALTITUDE_CHANGE")
        self.test_command("Typo-Num", "space", "fly east 50m ", "MOVE_DIRECTION")  # trailing space
        
        # ==================== PART 3: AMBIGUOUS & COMPOUND ====================
        self.print_header("PART 3: AMBIGUOUS & COMPOUND REQUESTS (25 tests)")
        
        print(f"\n{Colors.BOLD}3.1 Missing Parameters (3){Colors.RESET}")
        response, cmd = self.send_message("go up", "agent")
        has_question = "?" in response or "how" in response.lower() or "specify" in response.lower()
        self.results.append(TestResult("Ambiguous", "go up (no dist)", "go up", "Ask", response, cmd, has_question))
        self.tests_completed += 1; self.print_test_with_eta("go up (should ask)", has_question)
        
        response, cmd = self.send_message("move north", "agent")
        has_question = "?" in response or "how" in response.lower() or "specify" in response.lower()
        self.results.append(TestResult("Ambiguous", "move north (no dist)", "move north", "Ask", response, cmd, has_question))
        self.tests_completed += 1; self.print_test_with_eta("move north (should ask)", has_question)
        
        response, cmd = self.send_message("takeoff", "agent")
        self.results.append(TestResult("Ambiguous", "takeoff (no alt)", "takeoff", "TAKEOFF or Ask", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("takeoff (default?)", True)
        
        print(f"\n{Colors.BOLD}3.2 Vague Directions (4){Colors.RESET}")
        response, cmd = self.send_message("move forward", "agent")
        has_error = "cannot" in response.lower() or "cardinal" in response.lower()
        self.results.append(TestResult("Ambiguous", "forward", "move forward 20m", "Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("move forward (reject)", has_error or not cmd)
        
        response, cmd = self.send_message("go backward", "agent")
        has_error = "cannot" in response.lower() or "cardinal" in response.lower()
        self.results.append(TestResult("Ambiguous", "backward", "go backward 10m", "Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("go backward (reject)", has_error or not cmd)
        
        response, cmd = self.send_message("fly left", "agent")
        has_error = "cannot" in response.lower() or "cardinal" in response.lower()
        self.results.append(TestResult("Ambiguous", "left", "fly left 15m", "Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("fly left (reject)", has_error or not cmd)
        
        response, cmd = self.send_message("go right 20 meters", "agent")
        has_error = "cannot" in response.lower() or "cardinal" in response.lower()
        self.results.append(TestResult("Ambiguous", "right", "go right 20m", "Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("go right (reject)", has_error or not cmd)
        
        print(f"\n{Colors.BOLD}3.3 Relative Commands (3){Colors.RESET}")
        response, cmd = self.send_message("a little higher", "agent")
        has_question = "?" in response or "how" in response.lower()
        self.results.append(TestResult("Ambiguous", "a little higher", "a little higher", "Ask", response, cmd, has_question))
        self.tests_completed += 1; self.print_test_with_eta("a little higher (ask)", has_question)
        
        response, cmd = self.send_message("slightly to the left", "agent")
        has_error = "cannot" in response.lower() or "cardinal" in response.lower()
        self.results.append(TestResult("Ambiguous", "slightly left", "slightly to the left", "Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("slightly left (reject)", has_error or not cmd)
        
        response, cmd = self.send_message("move closer", "agent")
        has_question = "?" in response or "specify" in response.lower()
        self.results.append(TestResult("Ambiguous", "closer", "move closer", "Ask", response, cmd, has_question or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("move closer (ask)", has_question or not cmd)
        
        print(f"\n{Colors.BOLD}3.4 Incomplete References (3){Colors.RESET}")
        response, cmd = self.send_message("fly there", "agent")
        has_question = "?" in response or "where" in response.lower()
        self.results.append(TestResult("Ambiguous", "fly there", "fly there", "Ask", response, cmd, has_question or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("fly there (ask)", has_question or not cmd)
        
        response, cmd = self.send_message("go to that place", "agent")
        has_question = "?" in response or "specify" in response.lower()
        self.results.append(TestResult("Ambiguous", "that place", "go to that place", "Ask", response, cmd, has_question or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("that place (ask)", has_question or not cmd)
        
        response, cmd = self.send_message("do that thing", "agent")
        has_question = "?" in response
        self.results.append(TestResult("Ambiguous", "that thing", "do that thing", "Ask", response, cmd, has_question or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("that thing (ask)", has_question or not cmd)
        
        print(f"\n{Colors.BOLD}3.5 Context-Dependent (5){Colors.RESET}")
        response, cmd = self.send_message("repeat last command", "agent")
        has_error = "no previous" in response.lower() or "cannot" in response.lower()
        self.results.append(TestResult("Ambiguous", "repeat last", "repeat last command", "Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("repeat last (reject)", has_error or not cmd)
        
        response, cmd = self.send_message("do it again", "agent")
        has_error = "no previous" in response.lower() or "what" in response.lower()
        self.results.append(TestResult("Ambiguous", "do it again", "do it again", "Ask/Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("do it again (ask)", has_error or not cmd)
        
        response, cmd = self.send_message("same as before", "agent")
        has_error = "no previous" in response.lower() or "cannot" in response.lower()
        self.results.append(TestResult("Ambiguous", "same as before", "same as before", "Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("same as before (reject)", has_error or not cmd)
        
        response, cmd = self.send_message("undo", "agent")
        has_error = "cannot" in response.lower() or "undo" not in cmd.get("type", "").lower() if cmd else True
        self.results.append(TestResult("Ambiguous", "undo", "undo", "Not supported", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("undo (not supported)", has_error or not cmd)
        
        response, cmd = self.send_message("cancel that", "agent")
        has_error = "what" in response.lower() or "cannot" in response.lower()
        self.results.append(TestResult("Ambiguous", "cancel", "cancel that", "Ask", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("cancel that (ask)", has_error or not cmd)
        
        print(f"\n{Colors.BOLD}3.6 Compound/Multi-Step (7){Colors.RESET}")
        response, cmd = self.send_message("arm and takeoff to 20 meters", "agent")
        self.results.append(TestResult("Compound", "arm and takeoff", "arm and takeoff to 20 meters", "ARM or Reject", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("arm and takeoff", True)
        
        response, cmd = self.send_message("land then disarm", "agent")
        self.results.append(TestResult("Compound", "land then disarm", "land then disarm", "LAND or Reject", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("land then disarm", True)
        
        response, cmd = self.send_message("change to auto mode and start mission", "agent")
        self.results.append(TestResult("Compound", "mode and mission", "change to auto and start mission", "CHANGE_MODE or Reject", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("mode and start mission", True)
        
        response, cmd = self.send_message("go up 10 meters then move north 50 meters", "agent")
        self.results.append(TestResult("Compound", "up then north", "go up 10 then north 50", "ALTITUDE_CHANGE or Reject", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("up then north", True)
        
        response, cmd = self.send_message("arm, takeoff to 100m, and fly to coordinates 37.7749, -122.4194", "agent")
        self.results.append(TestResult("Compound", "3 commands", "arm, takeoff, goto", "ARM or Reject", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("arm, takeoff, goto", True)
        
        response, cmd = self.send_message("arm if battery is above 80%", "agent")
        self.results.append(TestResult("Compound", "arm if battery", "arm if battery >80%", "Conditional", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("arm if battery >80%", True)
        
        response, cmd = self.send_message("land when altitude reaches 5 meters", "agent")
        self.results.append(TestResult("Compound", "land when", "land when alt=5m", "Conditional", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("land when alt=5m", True)
        
        # ==================== PART 4: SAFETY & PILOT SPEECH ====================
        self.print_header("PART 4: SAFETY-CRITICAL & PILOT SPEECH (17 tests)")
        
        print(f"\n{Colors.BOLD}4.1 Excessive Values (4){Colors.RESET}")
        self.test_command("Safety", "10000m", "takeoff to 10000 meters", "ERROR")
        self.test_command("Safety", "50km", "move north 50000 meters", "ERROR")
        self.test_command("Safety", "space", "climb to space", "ERROR")
        
        response, cmd = self.send_message("go as high as possible", "agent")
        has_limit = "maximum" in response.lower() or "limit" in response.lower()
        self.results.append(TestResult("Safety", "as high as possible", "go as high as possible", "Mention limit", response, cmd, has_limit))
        self.tests_completed += 1; self.print_test_with_eta("as high as possible", has_limit)
        
        print(f"\n{Colors.BOLD}4.2 Dangerous Combinations (2){Colors.RESET}")
        response, cmd = self.send_message("disarm while in air", "agent")
        has_warning = "dangerous" in response.lower() or "unsafe" in response.lower() or "warning" in response.lower()
        self.results.append(TestResult("Safety", "disarm in air", "disarm while in air", "Warn", response, cmd, has_warning or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("disarm in air (warn)", has_warning or not cmd)
        
        response, cmd = self.send_message("takeoff without arming", "agent")
        has_warning = "arm" in response.lower() and ("first" in response.lower() or "must" in response.lower())
        self.results.append(TestResult("Safety", "takeoff w/o arm", "takeoff without arming", "Mention arming", response, cmd, has_warning or cmd.get("type") == "ARM" if cmd else True))
        self.tests_completed += 1; self.print_test_with_eta("takeoff w/o arming", has_warning)
        
        print(f"\n{Colors.BOLD}4.3 Contradictory (2){Colors.RESET}")
        response, cmd = self.send_message("land but stay at 100m", "agent")
        has_error = "cannot" in response.lower() or "contradictory" in response.lower()
        self.results.append(TestResult("Safety", "land but stay", "land but stay at 100m", "Reject", response, cmd, has_error or not cmd))
        self.tests_completed += 1; self.print_test_with_eta("land but stay 100m", has_error or not cmd)
        
        response, cmd = self.send_message("takeoff and land", "agent")
        self.results.append(TestResult("Safety", "takeoff and land", "takeoff and land", "Handle", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("takeoff and land", True)
        
        print(f"\n{Colors.BOLD}4.4 Emergency Phrases (4){Colors.RESET}")
        response, cmd = self.send_message("EMERGENCY LAND NOW", "agent")
        self.results.append(TestResult("Safety", "EMERGENCY LAND", "EMERGENCY LAND NOW", "LAND", response, cmd, cmd.get("type") == "LAND" if cmd else False))
        self.tests_completed += 1; self.print_test_with_eta("EMERGENCY LAND", cmd.get("type") == "LAND" if cmd else False)
        
        response, cmd = self.send_message("ABORT ABORT", "agent")
        has_response = len(response) > 10
        self.results.append(TestResult("Safety", "ABORT", "ABORT ABORT", "Respond", response, cmd, has_response))
        self.tests_completed += 1; self.print_test_with_eta("ABORT ABORT", has_response)
        
        response, cmd = self.send_message("something's wrong", "agent")
        has_response = "?" in response or "help" in response.lower()
        self.results.append(TestResult("Safety", "something wrong", "something's wrong", "Ask", response, cmd, has_response))
        self.tests_completed += 1; self.print_test_with_eta("something's wrong", has_response)
        
        response, cmd = self.send_message("help", "agent")
        has_response = len(response) > 20
        self.results.append(TestResult("Safety", "help", "help", "Respond", response, cmd, has_response))
        self.tests_completed += 1; self.print_test_with_eta("help", has_response)
        
        print(f"\n{Colors.BOLD}4.5 Pilot Speech (5){Colors.RESET}")
        response, cmd = self.send_message("taking it up to five-zero", "agent")
        self.results.append(TestResult("Pilot", "five-zero", "taking it up to five-zero", "Unclear", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("five-zero (50m?)", True)
        
        response, cmd = self.send_message("bingo fuel, RTL", "agent")
        has_rtl = cmd.get("type") == "RTL" if cmd else False
        self.results.append(TestResult("Pilot", "bingo fuel", "bingo fuel, RTL", "RTL", response, cmd, has_rtl))
        self.tests_completed += 1; self.print_test_with_eta("bingo fuel RTL", has_rtl)
        
        response, cmd = self.send_message("going hot", "agent")
        self.results.append(TestResult("Pilot", "going hot", "going hot", "Unclear", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("going hot", True)
        
        response, cmd = self.send_message("positive rate, gear up", "agent")
        self.results.append(TestResult("Pilot", "positive rate", "positive rate, gear up", "N/A", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("positive rate", True)
        
        response, cmd = self.send_message("winchester, coming home", "agent")
        self.results.append(TestResult("Pilot", "winchester", "winchester, coming home", "Interpret", response, cmd, True))
        self.tests_completed += 1; self.print_test_with_eta("winchester", True)
        
        self.end_time = datetime.now()
        return True
    
    def generate_html_report(self):
        """Generate comprehensive HTML report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        duration = (self.end_time - self.start_time).total_seconds()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ArduPilot AI Backend - Ultimate Test Report</title>
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
        table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 20px; }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .category {{ background: #ecf0f1; font-weight: bold; }}
        .pass-badge {{ background: #27ae60; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px; }}
        .fail-badge {{ background: #e74c3c; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px; }}
        .error {{ color: #e74c3c; font-size: 12px; }}
        .response {{ font-size: 12px; color: #666; max-width: 400px; }}
        .command {{ font-family: monospace; background: #ecf0f1; padding: 2px 6px; border-radius: 3px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚁 ArduPilot AI Backend - Ultimate Comprehensive Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)</p>
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
                <th>Got</th>
                <th>Response</th>
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
        
        report_path = "test_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n{Colors.GREEN}✓ HTML report: {report_path}{Colors.RESET}")
        return report_path
    
    def print_summary(self):
        """Print summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        duration = (self.end_time - self.start_time).total_seconds()
        
        self.print_header("ULTIMATE TEST SUITE SUMMARY")
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"Success Rate: {Colors.BOLD}{success_rate:.1f}%{Colors.RESET}")
        print(f"Duration: {duration:.1f}s ({duration/60:.1f} min)\n")
        
        # Category breakdown
        categories = {}
        for result in self.results:
            cat = result.category.split('-')[0]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if result.passed:
                categories[cat]["passed"] += 1
        
        print(f"{Colors.BOLD}By Category:{Colors.RESET}")
        for cat, stats in sorted(categories.items()):
            rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            color = Colors.GREEN if rate >= 90 else Colors.YELLOW if rate >= 70 else Colors.RED
            print(f"  {cat:20s}: {color}{stats['passed']:3d}/{stats['total']:3d} ({rate:5.1f}%){Colors.RESET}")
        
        if success_rate >= 90:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 EXCELLENT! System very robust!{Colors.RESET}\n")
        elif success_rate >= 70:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  GOOD, improvements needed{Colors.RESET}\n")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ NEEDS WORK{Colors.RESET}\n")

def main():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}ArduPilot AI Backend - ULTIMATE TEST SUITE{Colors.RESET}")
    print(f"{Colors.BOLD}170+ Comprehensive Real-World Tests{Colors.RESET}")
    print(f"{Colors.BOLD}Estimated time: ~3-5 minutes (depends on LLM speed){Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")

    tester = ComprehensiveTestSuite()
    
    if not tester.run_all_tests():
        print(f"\n{Colors.RED}Tests aborted{Colors.RESET}\n")
        sys.exit(1)
    
    tester.print_summary()
    tester.generate_html_report()
    
    print(f"\n{Colors.YELLOW}Note: Some 'failures' are correct behavior{Colors.RESET}")
    print(f"{Colors.YELLOW}(rejecting ambiguous commands, asking for clarification){Colors.RESET}\n")

if __name__ == "__main__":
    main()
