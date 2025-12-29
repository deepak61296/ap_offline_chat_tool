# Installation Guide - Linux

## Overview

This guide provides step-by-step instructions for installing the ArduPilot Offline AI Assistant on Linux systems. The installation is modular to ensure compatibility across different Linux distributions.

> **⚠️ IMPORTANT DISCLAIMER**  
> This is a **Stage 1 prototype** for testing and development purposes only.  
> **DO NOT use with real drones in production environments.**  
> Use at your own risk. Always test in simulation (SITL) first.

## Prerequisites

- Linux distribution (Ubuntu 20.04+ recommended)
- Internet connection (for initial setup only)
- 4GB RAM minimum, 8GB recommended
- 5GB free disk space

## Installation Steps

### Step 1: Install Miniconda

Miniconda provides a lightweight Python environment manager.

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Make it executable
chmod +x Miniconda3-latest-Linux-x86_64.sh

# Run installer
./Miniconda3-latest-Linux-x86_64.sh

# Follow prompts:
# - Press ENTER to review license
# - Type 'yes' to accept
# - Press ENTER to confirm location
# - Type 'yes' to initialize Miniconda

# Restart terminal or run:
source ~/.bashrc

# Verify installation
conda --version
```

**Download Link**: https://docs.conda.io/en/latest/miniconda.html

### Step 2: Create Conda Environment

```bash
# Create environment with Python 3.10
conda create -n ap_chat_tools python=3.10 -y

# Activate environment
conda activate ap_chat_tools

# Verify Python version
python --version  # Should show Python 3.10.x
```

### Step 3: Clone Repository

```bash
# Navigate to your projects directory
cd ~/Documents  # or your preferred location

# Clone the repository
git clone https://github.com/deepak61296/ap_offline_chat_tool.git

# Enter directory
cd ap_offline_chat_tool
```

### Step 4: Install Python Dependencies

```bash
# Make sure environment is activated
conda activate ap_chat_tools

# Install requirements
pip install -r requirements.txt

# Verify installation
python -c "import pymavlink, rich; print('Dependencies installed successfully')"
```

### Step 5: Install Ollama

Ollama hosts the AI model locally.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# Start Ollama service (if not auto-started)
ollama serve &
```

**Download Link**: https://ollama.com/download/linux

### Step 6: Pull the AI Model

```bash
# Pull the fine-tuned model (552MB download)
ollama pull deepakpopli/ardupilot-stage1

# Verify model is available
ollama list | grep ardupilot-stage1
```

This downloads the Stage 1 model optimized for basic drone commands.

### Step 7: Test Demo Mode

Demo mode works without ArduPilot SITL - perfect for testing the AI assistant.

```bash
# Make sure you're in the project directory
cd ~/Documents/ap_offline_chat_tool

# Activate environment
conda activate ap_chat_tools

# Run demo
python examples/demo.py
```

**Try these commands:**
- `arm the drone`
- `takeoff to 15 meters`
- `check battery status`
- `where am I?`
- `/quit` to exit

If demo mode works, your installation is successful!

## Optional: ArduPilot SITL Setup

**Only needed if you want to test with real simulation or hardware.**

### Step 8: Install ArduPilot SITL (Optional)

```bash
# Clone ArduPilot repository
cd ~
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot

# Checkout stable version
git checkout Copter-4.5
git submodule update --init --recursive

# Install prerequisites
Tools/environment_install/install-prereqs-ubuntu.sh -y

# Build ArduCopter SITL
cd ArduCopter
../Tools/scripts/waf configure --board sitl
../Tools/scripts/waf build

# Test SITL
sim_vehicle.py -w
```

**Official Documentation**: https://ardupilot.org/dev/docs/building-setup-linux.html

### Step 9: Run with SITL

```bash
# Terminal 1: Start SITL
cd ~/ardupilot/ArduCopter
sim_vehicle.py -w --console --map

# Terminal 2: Start AI Assistant
cd ~/Documents/ap_offline_chat_tool
conda activate ap_chat_tools
python main.py
```

## Verification

Run the test suite to verify everything works:

```bash
# Activate environment
conda activate ap_chat_tools

# Run tests
python tests/test_suite.py

# Expected output:
# Total Tests: 20
# [PASS] Passed: 20
# Success Rate: 100.0%
```

## Troubleshooting

### Conda command not found

```bash
# Add conda to PATH
export PATH="$HOME/miniconda3/bin:$PATH"
source ~/.bashrc
```

### Ollama connection error

```bash
# Start Ollama service
ollama serve &

# Wait a few seconds, then try again
sleep 5
ollama list
```

### Model download fails

```bash
# Check internet connection
ping -c 3 ollama.com

# Try pulling again
ollama pull deepakpopli/ardupilot-stage1
```

### Import errors

```bash
# Reinstall dependencies
conda activate ap_chat_tools
pip install --force-reinstall -r requirements.txt
```

## Quick Reference

```bash
# Activate environment
conda activate ap_chat_tools

# Run demo mode
python examples/demo.py

# Run with SITL
python main.py

# Run tests
python tests/test_suite.py

# Deactivate environment
conda deactivate
```

## Next Steps

- Read [COMMAND_REFERENCE.md](COMMAND_REFERENCE.md) for supported commands
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common usage patterns
- Check [README.md](../README.md) for project overview

## Support

- **Issues**: https://github.com/deepak61296/ap_offline_chat_tool/issues
- **Documentation**: [docs/](.)
- **ArduPilot Docs**: https://ardupilot.org/

---

**Remember**: This is a Stage 1 prototype. Always test in simulation before real flights!
