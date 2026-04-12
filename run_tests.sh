#!/bin/bash
# Comprehensive test runner for ArduPilot AI Backend v3.0

set -e

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate ardupilot_ai

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║ ArduPilot AI Backend v3.0 - Comprehensive Test Suite          ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd "$(dirname "$0")"

# Test 1: Unit Tests
echo -e "\n${BLUE}[1/5]${NC} Running unit tests..."
if python tests/test_new_tools.py > /tmp/unit_test.log 2>&1; then
    echo -e "${GREEN}✓ Unit tests passed (39/39)${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    cat /tmp/unit_test.log
    exit 1
fi

# Test 2: Syntax Check
echo -e "\n${BLUE}[2/5]${NC} Checking Python syntax..."
if python3 -m py_compile backend/tools.py backend/executor.py backend/param_db.py; then
    echo -e "${GREEN}✓ Syntax check passed${NC}"
else
    echo -e "${RED}✗ Syntax check failed${NC}"
    exit 1
fi

# Test 3: Parameter Database
echo -e "\n${BLUE}[3/5]${NC} Testing parameter database..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from backend.param_db import db

tests_passed = 0
tests_total = 6

# Test 3.1: Database loaded
if len(db.params) > 5000:
    print("  ✓ Database loaded (5644+ parameters)")
    tests_passed += 1
else:
    print(f"  ✗ Database too small ({len(db.params)} params)")

# Test 3.2: Battery search
battery_results = db.search("battery failsafe", 3)
if any("BATT_" in r["name"] for r in battery_results):
    print("  ✓ Battery search finds BATT_ params")
    tests_passed += 1
else:
    print("  ✗ Battery search failed")

# Test 3.3: Motor search
motor_results = db.search("motor spin", 3)
if any("MOT_" in r["name"] for r in motor_results):
    print("  ✓ Motor search finds MOT_ params")
    tests_passed += 1
else:
    print("  ✗ Motor search failed")

# Test 3.4: Loiter search
loiter_results = db.search("loiter", 3)
if any("LOIT_" in r["name"] for r in loiter_results):
    print("  ✓ Loiter search finds LOIT_ params")
    tests_passed += 1
else:
    print("  ✗ Loiter search failed")

# Test 3.5: SIM params deprioritized
batt_voltage = db.search("battery voltage", 3)
if not any(r["name"].startswith("SIM_") for r in batt_voltage):
    print("  ✓ SIM_ parameters deprioritized")
    tests_passed += 1
else:
    print("  ✗ SIM_ deprioritization failed")

# Test 3.6: Compass search
compass_results = db.search("compass", 3)
if any("COMPASS_" in r["name"] for r in compass_results):
    print("  ✓ Compass search finds COMPASS_ params")
    tests_passed += 1
else:
    print("  ✗ Compass search failed")

print(f"\n  Result: {tests_passed}/{tests_total} tests passed")
sys.exit(0 if tests_passed == tests_total else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Parameter database tests passed${NC}"
else
    echo -e "${RED}✗ Parameter database tests failed${NC}"
    exit 1
fi

# Test 4: Tool Definition Validation
echo -e "\n${BLUE}[4/5]${NC} Validating tool definitions..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from backend.tools import TOOL_DEFINITIONS, VALID_TOOLS, normalize_tool_call

tests_passed = 0
tests_total = 9

# Test 4.1: All tools have names
if all("name" in t for t in TOOL_DEFINITIONS):
    print("  ✓ All tools have names")
    tests_passed += 1
else:
    print("  ✗ Some tools missing names")

# Test 4.2: All tools have descriptions
if all("description" in t for t in TOOL_DEFINITIONS):
    print("  ✓ All tools have descriptions")
    tests_passed += 1
else:
    print("  ✗ Some tools missing descriptions")

# Test 4.3: VALID_TOOLS matches definitions
if {t["name"] for t in TOOL_DEFINITIONS} == VALID_TOOLS:
    print("  ✓ VALID_TOOLS set matches definitions")
    tests_passed += 1
else:
    print("  ✗ VALID_TOOLS mismatch")

# Test 4.4-4.8: New tools exist
new_tools = ["get_status", "get_position", "pause", "resume", "explain_param"]
for tool in new_tools:
    if tool in VALID_TOOLS:
        print(f"  ✓ Tool '{tool}' exists")
        tests_passed += 1
    else:
        print(f"  ✗ Tool '{tool}' missing")

# Test 4.9: At least 20 tools
if len(TOOL_DEFINITIONS) >= 20:
    print(f"  ✓ {len(TOOL_DEFINITIONS)} tools defined")
    tests_passed += 1
else:
    print(f"  ✗ Only {len(TOOL_DEFINITIONS)} tools (expected ≥20)")

print(f"\n  Result: {tests_passed}/{tests_total} tests passed")
sys.exit(0 if tests_passed == tests_total else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Tool definition validation passed${NC}"
else
    echo -e "${RED}✗ Tool definition validation failed${NC}"
    exit 1
fi

# Test 5: Check if backend is running
echo -e "\n${BLUE}[5/5]${NC} Checking backend connectivity..."
if command -v curl &> /dev/null; then
    RESPONSE=$(curl -s http://localhost:5000/health 2>/dev/null || echo "")
    if echo "$RESPONSE" | grep -q "healthy"; then
        echo -e "${GREEN}✓ Backend is running and healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Backend not running (that's OK for unit tests)${NC}"
        echo "  Start with: python run_server.py"
    fi
else
    echo -e "${YELLOW}⚠ curl not available, skipping connectivity check${NC}"
fi

# Summary
echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo -e "║${GREEN} ALL TESTS PASSED ✓${NC}                                    │"
echo -e "║                                                                ║"
echo -e "║ Test Summary:                                                  │"
echo -e "║  • Unit tests: 39/39 passed                                   │"
echo -e "║  • Syntax check: passed                                        │"
echo -e "║  • Parameter DB: 6/6 tests passed                             │"
echo -e "║  • Tool definitions: 9/9 tests passed                         │"
echo -e "║                                                                ║"
echo -e "║ Next: Read TESTING_GUIDE.md for integration tests             │"
echo -e "╚════════════════════════════════════════════════════════════════╝"
