#!/bin/bash
# Quick verification script for ArduPilot Offline Chat Tool

echo "╔═══════════════════════════════════════════════════════╗"
echo "║   ArduPilot Offline Chat Tool - System Check         ║"
echo "║   Powered by FunctionGemma (270M)                     ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Running system verification...${NC}\n"

# Run verification
python tests/test_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║              ✅ ALL SYSTEMS GO! ✅                    ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${GREEN}🎉 Ready to fly!${NC}"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo "  Demo Mode (no SITL):   python demo.py"
    echo "  With SITL:             python main.py"
    echo ""
else
    echo ""
    echo "❌ Some checks failed. Fix issues above."
    exit 1
fi
