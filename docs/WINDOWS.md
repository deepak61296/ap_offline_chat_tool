# Windows Installation Guide

## ArduPilot AI Assistant on Windows

This guide helps Windows users set up and run the ArduPilot AI Assistant.

## Prerequisites

### Required Software

1. **Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop/
   - Requires Windows 10/11 Pro, Enterprise, or Education (64-bit)
   - Enable WSL 2 backend during installation

2. **Git for Windows** (optional, for cloning)
   - Download: https://git-scm.com/download/win
   - Or use GitHub Desktop: https://desktop.github.com/

3. **Windows Terminal** (recommended)
   - Install from Microsoft Store
   - Better terminal experience than CMD

## Quick Start (Windows)

### Option 1: Using Docker Desktop

**Step 1: Install Docker Desktop**

```powershell
# Download and install Docker Desktop
# https://www.docker.com/products/docker-desktop/

# After installation, restart your computer
# Open Docker Desktop and wait for it to start
```

**Step 2: Clone the Repository**

```powershell
# Open PowerShell or Windows Terminal
cd C:\Users\YourUsername\Documents

# Clone the repository
git clone https://github.com/deepak61296/ap_offline_chat_tool.git
cd ap_offline_chat_tool
```

**Step 3: Build and Run**

```powershell
# Build the Docker image
docker build -t ap_offline_chat_tool .

# Run demo mode
docker run -it --rm ap_offline_chat_tool
```

### Option 2: Using Pre-built Image (Coming Soon)

```powershell
# Pull the image from Docker Hub
docker pull deepak61296/ap_offline_chat_tool

# Run it
docker run -it --rm deepak61296/ap_offline_chat_tool
```

## Running the Assistant

### Demo Mode (No SITL)

```powershell
# Run interactive demo
docker run -it --rm ap_offline_chat_tool

# Try commands:
# - arm the drone
# - takeoff 20
# - check battery
# - /quit to exit
```

### With Persistent Model Storage

```powershell
# Create a volume for Ollama models
docker volume create ollama-models

# Run with persistent storage
docker run -it --rm `
  -v ollama-models:/home/ardupilot/.ollama `
  ap_offline_chat_tool
```

**Note**: In PowerShell, use backtick (`) for line continuation. In CMD, use caret (^).

### Running Tests

```powershell
# Run all tests
docker run --rm ap_offline_chat_tool python3 tests/test_suite.py

# Run preprocessing tests
docker run --rm ap_offline_chat_tool python3 tests/test_preprocessing.py
```

## Windows-Specific Notes

### WSL 2 Backend

Docker Desktop on Windows uses WSL 2. Make sure it's enabled:

1. Open Docker Desktop
2. Go to Settings → General
3. Check "Use the WSL 2 based engine"

### File Paths

Windows uses backslashes (`\`) but Docker uses forward slashes (`/`). When mounting volumes:

```powershell
# Correct way to mount Windows paths
docker run -v C:/Users/YourName/data:/data ap_offline_chat_tool

# Or use PowerShell's automatic conversion
docker run -v ${PWD}:/app ap_offline_chat_tool
```

### Line Endings

If you edit files on Windows, be aware of line ending differences:

```powershell
# Configure Git to handle line endings
git config --global core.autocrlf true
```

### Firewall

Windows Firewall may prompt you to allow Docker. Click "Allow access" when prompted.

## Native Windows Installation (Advanced)

If you prefer running without Docker:

### Step 1: Install Python

```powershell
# Download Python 3.10+ from python.org
# https://www.python.org/downloads/

# Verify installation
python --version
```

### Step 2: Install Ollama

```powershell
# Download Ollama for Windows
# https://ollama.com/download/windows

# Install and verify
ollama --version
```

### Step 3: Install Dependencies

```powershell
# Clone the repository
git clone https://github.com/deepak61296/ap_offline_chat_tool.git
cd ap_offline_chat_tool

# Install Python packages
pip install -r requirements.txt
```

### Step 4: Get the Model

```powershell
# Pull the model
ollama pull deepakpopli/ardupilot-stage1
```

### Step 5: Run Demo Mode

```powershell
# Run the demo
python examples/demo.py
```

### For SITL Mode (Advanced)

SITL on Windows requires WSL or Cygwin. **Docker is recommended** for SITL on Windows.

## Troubleshooting (Windows)

### Docker Desktop Won't Start

**Problem**: Docker Desktop fails to start

**Solutions**:
1. Enable Hyper-V and WSL 2:
   ```powershell
   # Run as Administrator
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```
2. Restart your computer
3. Update WSL: `wsl --update`

### "Access Denied" Errors

**Problem**: Permission errors when running Docker

**Solutions**:
1. Run PowerShell/Terminal as Administrator
2. Add your user to the `docker-users` group:
   - Open Computer Management
   - Go to Local Users and Groups → Groups
   - Double-click `docker-users`
   - Add your user account
   - Log out and log back in

### Slow Performance

**Problem**: Docker runs slowly on Windows

**Solutions**:
1. Allocate more resources to Docker:
   - Open Docker Desktop
   - Settings → Resources
   - Increase CPU and Memory
2. Use WSL 2 backend (faster than Hyper-V)
3. Store project files in WSL filesystem for better performance

### Model Download Fails

**Problem**: Ollama can't download the model

**Solutions**:
1. Check internet connection
2. Check Windows Firewall settings
3. Try downloading manually:
   ```powershell
   ollama pull deepakpopli/ardupilot-stage1
   ```

### Line Ending Issues

**Problem**: Scripts fail with `\r` errors

**Solution**:
```powershell
# Convert line endings
git config --global core.autocrlf true
git clone https://github.com/deepak61296/ap_offline_chat_tool.git
```

## PowerShell vs CMD

### PowerShell (Recommended)

```powershell
# Multi-line commands use backtick
docker run -it --rm `
  -v ollama-models:/home/ardupilot/.ollama `
  ap_offline_chat_tool
```

### Command Prompt (CMD)

```cmd
REM Multi-line commands use caret
docker run -it --rm ^
  -v ollama-models:/home/ardupilot/.ollama ^
  ap_offline_chat_tool
```

## Windows Terminal Tips

### Better Experience

1. Install Windows Terminal from Microsoft Store
2. Set PowerShell as default shell
3. Enable copy/paste with Ctrl+C/Ctrl+V:
   - Settings → Actions
   - Enable "Copy on select"

### Keyboard Shortcuts

- `Ctrl + Shift + T`: New tab
- `Ctrl + Shift + W`: Close tab
- `Ctrl + ,`: Open settings
- `Alt + Shift + D`: Split pane

## Development on Windows

### Using VS Code

```powershell
# Install VS Code
# https://code.visualstudio.com/

# Install Docker extension
code --install-extension ms-azuretools.vscode-docker

# Open project
code .
```

### Remote Development

Use VS Code's Remote - Containers extension to develop inside the Docker container:

1. Install "Remote - Containers" extension
2. Open project folder
3. Click "Reopen in Container"
4. VS Code runs inside the Docker container!

## Performance Tips

### Use WSL 2 Filesystem

For better performance, store your project in WSL 2:

```powershell
# Access WSL from Windows
\\wsl$\Ubuntu\home\username\projects

# Or use WSL directly
wsl
cd ~/projects
git clone https://github.com/deepak61296/ap_offline_chat_tool.git
```

### Allocate Resources

```powershell
# Edit .wslconfig in your home directory
notepad $env:USERPROFILE\.wslconfig

# Add these settings:
[wsl2]
memory=4GB
processors=2
```

## Comparison: Docker vs Native

### Docker (Recommended)

**Pros:**
- ✅ Consistent environment
- ✅ Easy setup
- ✅ Includes all dependencies
- ✅ Works on all Windows versions

**Cons:**
- ❌ Requires Docker Desktop
- ❌ Slightly slower than native
- ❌ Uses more disk space

### Native Installation

**Pros:**
- ✅ Faster performance
- ✅ No Docker required
- ✅ Direct access to files

**Cons:**
- ❌ Manual dependency management
- ❌ SITL requires WSL/Cygwin
- ❌ More complex setup

## Next Steps

Once you have the assistant running:

1. **Try the demo**: `docker run -it --rm ap_offline_chat_tool`
2. **Read the docs**: See [README.md](../README.md)
3. **Check commands**: See [COMMAND_REFERENCE.md](COMMAND_REFERENCE.md)
4. **Run tests**: `docker run --rm ap_offline_chat_tool python3 tests/test_suite.py`

## Getting Help

- **Documentation**: [docs/](../docs/)
- **Issues**: https://github.com/deepak61296/ap_offline_chat_tool/issues
- **Docker Help**: https://docs.docker.com/desktop/windows/

---

**Windows users**: Docker is the recommended approach for the best experience!
