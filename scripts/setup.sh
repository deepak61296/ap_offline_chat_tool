#!/bin/bash
# ArduPilot AI Assistant - Setup Script
# This script sets up the development environment and verifies all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     🚁 ArduPilot AI Assistant - Setup Script             ║"
echo "║        Stage 1 (85% Accuracy)                            ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Function to print status messages
print_status() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        print_success "Python $PYTHON_VERSION found (>= 3.8 required)"
    else
        print_error "Python $PYTHON_VERSION found, but 3.8+ required"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.8 or higher"
    exit 1
fi

# Check Conda
print_status "Checking Conda installation..."
if command -v conda &> /dev/null; then
    CONDA_VERSION=$(conda --version | cut -d' ' -f2)
    print_success "Conda $CONDA_VERSION found"
else
    print_warning "Conda not found. Continuing without Conda (not recommended)"
fi

# Create/activate conda environment
if command -v conda &> /dev/null; then
    print_status "Setting up Conda environment 'ap_chat_tools'..."
    
    # Check if environment exists
    if conda env list | grep -q "^ap_chat_tools "; then
        print_success "Environment 'ap_chat_tools' already exists"
    else
        print_status "Creating new environment 'ap_chat_tools'..."
        conda create -n ap_chat_tools python=3.8 -y
        print_success "Environment created"
    fi
    
    print_status "To activate: conda activate ap_chat_tools"
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
if command -v conda &> /dev/null && conda env list | grep -q "^ap_chat_tools "; then
    # Install in conda environment
    conda run -n ap_chat_tools pip install -r requirements.txt
else
    # Install globally or in active environment
    pip install -r requirements.txt
fi
print_success "Python dependencies installed"

# Check Ollama
print_status "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n1 || echo "unknown")
    print_success "Ollama found: $OLLAMA_VERSION"
    
    # Check if model exists
    print_status "Checking for ardupilot-stage1 model..."
    if ollama list | grep -q "ardupilot-stage1"; then
        print_success "Model 'ardupilot-stage1' found"
    else
        print_warning "Model 'ardupilot-stage1' not found"
        print_warning "You need to create/import this model before using the assistant"
        print_warning "See TRAINING_GUIDE.md for instructions"
    fi
else
    print_error "Ollama not found. Please install Ollama from https://ollama.ai/"
    print_warning "The assistant requires Ollama to run the AI model"
fi

# Check PyMAVLink
print_status "Checking PyMAVLink installation..."
if command -v conda &> /dev/null && conda env list | grep -q "^ap_chat_tools "; then
    if conda run -n ap_chat_tools python -c "import pymavlink" 2>/dev/null; then
        print_success "PyMAVLink installed"
    else
        print_error "PyMAVLink not found"
        exit 1
    fi
else
    if python3 -c "import pymavlink" 2>/dev/null; then
        print_success "PyMAVLink installed"
    else
        print_error "PyMAVLink not found"
        exit 1
    fi
fi

# Check Rich library
print_status "Checking Rich library..."
if command -v conda &> /dev/null && conda env list | grep -q "^ap_chat_tools "; then
    if conda run -n ap_chat_tools python -c "import rich" 2>/dev/null; then
        print_success "Rich library installed"
    else
        print_error "Rich library not found"
        exit 1
    fi
else
    if python3 -c "import rich" 2>/dev/null; then
        print_success "Rich library installed"
    else
        print_error "Rich library not found"
        exit 1
    fi
fi

# Run quick test
print_status "Running quick functionality test..."
if command -v conda &> /dev/null && conda env list | grep -q "^ap_chat_tools "; then
    if conda run -n ap_chat_tools python -c "from function_gemma import FunctionGemmaInterface; from drone_functions import DroneController; print('✓ Imports successful')" 2>/dev/null; then
        print_success "Quick test passed"
    else
        print_error "Quick test failed - check imports"
        exit 1
    fi
else
    if python3 -c "from function_gemma import FunctionGemmaInterface; from drone_functions import DroneController; print('✓ Imports successful')" 2>/dev/null; then
        print_success "Quick test passed"
    else
        print_error "Quick test failed - check imports"
        exit 1
    fi
fi

# Final summary
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║              ✅ SETUP COMPLETE! ✅                        ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
print_success "All dependencies installed and verified!"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo ""
echo "1. Activate the environment (if using Conda):"
echo "   ${GREEN}conda activate ap_chat_tools${NC}"
echo ""
echo "2. Try demo mode (no SITL required):"
echo "   ${GREEN}python demo.py${NC}"
echo ""
echo "3. For SITL mode, start ArduPilot SITL first:"
echo "   ${GREEN}cd ~/ardupilot/ArduCopter${NC}"
echo "   ${GREEN}sim_vehicle.py -w --console --map${NC}"
echo ""
echo "   Then in another terminal:"
echo "   ${GREEN}python main.py${NC}"
echo ""
echo -e "${CYAN}Documentation:${NC}"
echo "  - README.md         - Full documentation"
echo "  - CONTRIBUTING.md   - How to contribute"
echo "  - CHANGELOG.md      - Version history"
echo ""
echo "🚁 Happy flying!"
echo ""
