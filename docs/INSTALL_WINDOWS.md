# Installation Guide - Windows

## Overview

This guide provides step-by-step instructions for installing the ArduPilot Offline AI Assistant on Windows systems.

> **⚠️ IMPORTANT**
> Always test thoroughly in simulation (SITL) before using with real hardware.

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
conda create -n ardupilot_ai python=3.10 -y

# Activate environment
conda activate ardupilot_ai

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
git clone https://github.com/deepak61296/ardupilot-ai-backend.git

# Enter directory
cd ardupilot-ai-backend
```

**Option B: Download ZIP**

1. Visit: https://github.com/deepak61296/ardupilot-ai-backend
2. Click "Code" → "Download ZIP"
3. Extract to `C:\Users\YourUsername\Documents\ardupilot-ai-backend`

### Step 4: Install Python Dependencies

```powershell
# Make sure environment is activated
conda activate ardupilot_ai

# Navigate to project directory
cd C:\Users\YourUsername\Documents\ardupilot-ai-backend

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
# Pull the default backend model
ollama pull qwen2.5:3b

# Verify model is available
ollama list
```

This downloads the Stage 1 model optimized for basic drone commands.

### Step 7: Test Demo Mode

Demo mode works without ArduPilot SITL - perfect for testing the AI assistant.

```powershell
# Navigate to project directory
cd C:\Users\YourUsername\Documents\ardupilot-ai-backend

# Activate environment
conda activate ardupilot_ai

# Test the API
curl http://localhost:5000/health
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
**Recommended**: Use Docker for SITL on Windows

### Option 1: Docker (Recommended)

```powershell
# Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop/

# Build Docker image
docker build -t ardupilot-ai-backend .

# Run with SITL (future feature)
docker run -it --rm --privileged --network host ardupilot-ai-backend sitl
```

### Option 2: WSL (Advanced)

1. **Enable WSL**:
   ```powershell
   # Run as Administrator
   wsl --install
   ```

2. **Install Ubuntu from Microsoft Store**

3. **Follow Linux installation guide inside WSL**:
   - Follow the ArduPilot SITL guide: https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html

**WSL Documentation**: https://learn.microsoft.com/en-us/windows/wsl/install

## Verification

Run the test suite to verify everything works:

```powershell
# Activate environment
conda activate ardupilot_ai

# Run tests
python tests\test_comprehensive.py
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
ollama pull qwen2.5:3b
```

### Import errors

```powershell
# Reinstall dependencies
conda activate ardupilot_ai
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
conda activate ardupilot_ai

# Test the API
curl http://localhost:5000/health

# Run tests
python tests\test_comprehensive.py

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

- Check [README.md](../README.md) for supported commands and usage examples
- See [ARCHITECTURE.md](../ARCHITECTURE.md) for system design
- See [COMPATIBILITY.md](../COMPATIBILITY.md) for version info

## Support

- **Issues**: https://github.com/deepak61296/ardupilot-ai-backend/issues
- **Documentation**: [README.md](../README.md)

---

**Remember**: Always test thoroughly in simulation before real flights!
