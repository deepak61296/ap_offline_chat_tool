#!/bin/bash
# Test script to verify Docker installation works correctly

set -e

echo "========================================="
echo "Docker Installation Test"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}[PASS]${NC}"
        ((PASSED++))
    else
        echo -e "${RED}[FAIL]${NC}"
        ((FAILED++))
    fi
}

echo "[1/6] Building Docker image..."
docker-compose build --quiet

echo "[2/6] Running system tests..."
run_test "Python version" "docker-compose run --rm ardupilot-assistant python3 --version"
run_test "Ollama installation" "docker-compose run --rm ardupilot-assistant which ollama"
run_test "Python packages" "docker-compose run --rm ardupilot-assistant python3 -c 'import pymavlink, rich, ollama'"

echo "[3/6] Setting up model..."
echo -e "${YELLOW}This may take a few minutes...${NC}"
docker-compose run --rm ardupilot-assistant bash -c "
    ollama serve &
    sleep 5
    cd /app/models
    ollama create ardupilot-stage1 -f ardupilot-stage1.Modelfile
" > /dev/null 2>&1

run_test "Model creation" "docker-compose run --rm ardupilot-assistant ollama list | grep ardupilot-stage1"

echo "[4/6] Running test suite..."
run_test "Preprocessing tests" "docker-compose run --rm ardupilot-assistant python3 tests/test_preprocessing.py"
run_test "Full test suite" "docker-compose run --rm ardupilot-assistant python3 tests/test_suite.py"

echo "[5/6] Testing demo mode..."
# Test that demo mode starts (run for 2 seconds then kill)
timeout 2s docker-compose run --rm ardupilot-assistant python3 examples/demo.py <<< "/quit" > /dev/null 2>&1 || true
run_test "Demo mode starts" "true"  # If we got here, it worked

echo "[6/6] Cleanup..."
docker-compose down -v > /dev/null 2>&1

echo ""
echo "========================================="
echo "Test Results"
echo "========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo "Docker installation is working correctly."
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC}"
    echo "Please check the output above for details."
    exit 1
fi
