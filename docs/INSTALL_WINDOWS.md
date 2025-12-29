# Installation Guide - Windows

## Overview

This guide provides step-by-step instructions for installing the ArduPilot Offline AI Assistant on Windows systems.

> **⚠️ IMPORTANT DISCLAIMER**  
> This is a **Stage 1 prototype** for testing and development purposes only.  
> **DO NOT use with real drones in production environments.**  
> Use at your own risk. Always test in simulation (SITL) first.

## Prerequisites

- Windows 10/11 (64-bit)
- Internet connection (for initial setup only)
- 4GB RAM minimum, 8GB recommended
- 5GB free disk space

## Installation Steps

### Step 1: Install Miniconda

Miniconda provides a lightweight Python environment manager for Windows.

1. **Download Miniconda**:
   - Visit: https://docs.conda.io/en/latest/miniconda.html
   - Download: `Miniconda3 Windows 64-bit`

2. **Run Installer**:
   - Double-click the downloaded `.exe` file
   - Click "Next" through the wizard
   - Choose "Just Me" (recommended)
   - Accept default installation location
   - **Important**: Check "Add Miniconda3 to PATH" (makes it easier)
   - Click "Install"

3. **Verify Installation**:
   ```powershell
   # Open PowerShell or Command Prompt
   conda --version
   ```

**Download Link**: https://docs.conda.io/en/latest/miniconda.html

### Step 2: Create Conda Environment

```powershell
# Open PowerShell or Command Prompt

# Create environment with Python 3.10
conda create -n ap_chat_tools python=3.10 -y

# Activate environment
conda activate ap_chat_tools

# Verify Python version
python --version
```

### Step 3: Clone Repository

**Option A: Using Git**

```powershell
# Install Git for Windows if not installed
# Download from: https://git-scm.com/download/win

# Navigate to your projects folder
cd C:\Users\YourUsername\Documents

# Clone repository
git clone https://github.com/deepak61296/ap_offline_chat_tool.git

# Enter directory
cd ap_offline_chat_tool
```

**Option B: Download ZIP**

1. Visit: https://github.com/deepak61296/ap_offline_chat_tool
2. Click "Code" → "Download ZIP"
3. Extract to `C:\Users\YourUsername\Documents\ap_offline_chat_tool`

### Step 4: Install Python Dependencies

```powershell
# Make sure environment is activated
conda activate ap_chat_tools

# Navigate to project directory
cd C:\Users\YourUsername\Documents\ap_offline_chat_tool

# Install requirements
pip install -r requirements.txt

# Verify installation
python -c "import pymavlink, rich; print('Dependencies installed successfully')"
```

### Step 5: Install Ollama

Ollama hosts the AI model locally on Windows.

1. **Download Ollama**:
   - Visit: https://ollama.com/download/windows
   - Download the Windows installer

2. **Install**:
   - Run the downloaded `.exe` file
   - Follow installation wizard
   - Ollama will start automatically

3. **Verify**:
   ```powershell
   ollama --version
   ```

**Download Link**: https://ollama.com/download/windows

### Step 6: Pull the AI Model

```powershell
# Pull the fine-tuned model (552MB download)
ollama pull deepakpopli/ardupilot-stage1

# Verify model is available
ollama list
```

This downloads the Stage 1 model optimized for basic drone commands.

### Step 7: Test Demo Mode

Demo mode works without ArduPilot SITL - perfect for testing the AI assistant.

```powershell
# Navigate to project directory
cd C:\Users\YourUsername\Documents\ap_offline_chat_tool

# Activate environment
conda activate ap_chat_tools

# Run demo
python examples\demo.py
```

**Try these commands:**
- `arm the drone`
- `takeoff to 15 meters`
- `check battery status`
- `where am I?`
- `/quit` to exit

If demo mode works, your installation is successful!

## Optional: ArduPilot SITL Setup

**⚠️ Note**: ArduPilot SITL on Windows requires WSL (Windows Subsystem for Linux) or Docker.  
**Recommended**: Use Docker for SITL on Windows (see [DOCKER.md](DOCKER.md))

### Option 1: Docker (Recommended)

```powershell
# Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop/

# Build Docker image
docker build -t ap_offline_chat_tool .

# Run with SITL (future feature)
docker run -it --rm --privileged --network host ap_offline_chat_tool sitl
```

### Option 2: WSL (Advanced)

1. **Enable WSL**:
   ```powershell
   # Run as Administrator
   wsl --install
   ```

2. **Install Ubuntu from Microsoft Store**

3. **Follow Linux installation guide inside WSL**:
   - See [INSTALL_LINUX.md](INSTALL_LINUX.md)

**WSL Documentation**: https://learn.microsoft.com/en-us/windows/wsl/install

## Verification

Run the test suite to verify everything works:

```powershell
# Activate environment
conda activate ap_chat_tools

# Run tests
python tests\test_suite.py

# Expected output:
# Total Tests: 20
# [PASS] Passed: 20
# Success Rate: 100.0%
```

## Troubleshooting

### Conda not recognized

```powershell
# Add Conda to PATH manually
# 1. Search for "Environment Variables" in Windows
# 2. Edit "Path" variable
# 3. Add: C:\Users\YourUsername\miniconda3
# 4. Add: C:\Users\YourUsername\miniconda3\Scripts
# 5. Restart PowerShell
```

### Ollama not starting

```powershell
# Check if Ollama is running
# Look for Ollama icon in system tray

# Restart Ollama
# Right-click Ollama icon → Quit
# Start Ollama from Start Menu
```

### Model download fails

```powershell
# Check internet connection
ping ollama.com

# Check Windows Firewall
# Allow Ollama through firewall if prompted

# Try pulling again
ollama pull deepakpopli/ardupilot-stage1
```

### Import errors

```powershell
# Reinstall dependencies
conda activate ap_chat_tools
pip install --force-reinstall -r requirements.txt
```

### PowerShell execution policy error

```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Quick Reference

```powershell
# Activate environment
conda activate ap_chat_tools

# Run demo mode
python examples\demo.py

# Run tests
python tests\test_suite.py

# Deactivate environment
conda deactivate
```

## Windows-Specific Notes

### File Paths
- Use backslashes: `C:\Users\YourName\Documents`
- Or forward slashes work too: `C:/Users/YourName/Documents`

### Line Endings
- Git handles line endings automatically
- If you see `\r` errors, run:
  ```powershell
  git config --global core.autocrlf true
  ```

### Antivirus
- Windows Defender may scan Ollama
- Add Ollama to exclusions if needed

## Next Steps

- Read [COMMAND_REFERENCE.md](COMMAND_REFERENCE.md) for supported commands
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common usage patterns
- Check [README.md](../README.md) for project overview
- For SITL, see [DOCKER.md](DOCKER.md)

## Support

- **Issues**: https://github.com/deepak61296/ap_offline_chat_tool/issues
- **Documentation**: [docs/](.)
- **Windows Help**: [WINDOWS.md](WINDOWS.md)

---

**Remember**: This is a Stage 1 prototype. Always test in simulation before real flights!
