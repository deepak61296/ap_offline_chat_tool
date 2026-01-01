# ArduPilot Offline AI Assistant

[![Stage 1 Complete](https://img.shields.io/badge/Stage%201-Complete-success)](https://github.com/deepak61296/ap_offline_chat_tool)
[![Model Accuracy](https://img.shields.io/badge/Accuracy-96%25-brightgreen)](https://ollama.com/library/qwen2.5)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)](docs/DOCKER.md)

> **Natural language drone control powered by AI - Fully offline, no API keys required**

A production-ready AI assistant that translates natural language commands into ArduPilot drone control actions using Qwen 2.5 (3B parameters). Control your drone through conversational commands without requiring internet connectivity or external API services.

## ⚠️ Important Disclaimer

**This is a Stage 1 prototype for testing and development purposes only.**

- **DO NOT use with real drones in production environments**
- **Always test in simulation (SITL) first**
- **Use at your own risk**
- This is a research project for prototyping natural language drone control
- Not certified for commercial or safety-critical applications

## Overview

This project provides an intelligent interface for ArduPilot-based drones, enabling operators to issue commands in natural language rather than through traditional ground control station interfaces. The system uses a locally-hosted AI model fine-tuned specifically for drone operations, ensuring reliable offline operation and data privacy.

**Key Capabilities:**
- Natural language command interpretation
- Real-time drone control via MAVLink protocol
- Comprehensive pre-flight safety checks
- Support for both simulation (SITL) and hardware deployment
- Extensible architecture for custom command sets

## Features

### Core Functionality

- **Natural Language Processing**: Issue commands in plain English (e.g., "arm the drone and takeoff to 15 meters")
- **Offline Operation**: Runs entirely on local hardware without internet dependency
- **Powerful AI Model**: Qwen 2.5 (3B parameters) for superior natural language understanding
- **High Accuracy**: 96% command interpretation accuracy across 38 functions
- **Safety Validation**: Built-in pre-flight checks and command validation
- **Dual Operation Modes**: 
  - Demo mode for testing without hardware
  - SITL mode for full simulation integration

### Technical Specifications

- **Model**: Qwen 2.5 (3B parameters)
- **Inference Engine**: Ollama (local deployment)
- **Function Library**: 38 drone control functions
- **Communication Protocol**: MAVLink via pymavlink
- **Supported Platforms**: Linux, Windows (macOS support planned)
- **Deployment Options**: Native installation or Docker containers

## Quick Start

### Choose Your Platform

**Linux Users**: See [docs/INSTALL_LINUX.md](docs/INSTALL_LINUX.md)  
**Windows Users**: See [docs/INSTALL_WINDOWS.md](docs/INSTALL_WINDOWS.md)  
**macOS Users**: Currently not supported (planned for future releases)

### Installation Overview

The installation is modular and platform-specific:

1. **Install Miniconda** - Python environment manager
   - Linux: https://docs.conda.io/en/latest/miniconda.html
   - Windows: https://docs.conda.io/en/latest/miniconda.html

2. **Create Conda Environment**
   ```bash
   conda create -n ap_chat_tools python=3.10 -y
   conda activate ap_chat_tools
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.com/deepak61296/ap_offline_chat_tool.git
   cd ap_offline_chat_tool
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Ollama**
   - Linux: https://ollama.com/download/linux
   - Windows: https://ollama.com/download/windows

6. **Pull AI Model**
   ```bash
   ollama pull qwen2.5:3b
   ```

7. **Test Demo Mode**
   ```bash
   python examples/demo.py
   ```

**For detailed step-by-step instructions**, see the platform-specific guides:
- [Linux Installation Guide](docs/INSTALL_LINUX.md)
- [Windows Installation Guide](docs/INSTALL_WINDOWS.md)

### Docker Installation (All Platforms)

For a containerized setup:

```bash
# Build the Docker image
docker build -t ap_offline_chat_tool .

# Run in demo mode
docker run -it --rm ap_offline_chat_tool

# Run tests
docker run --rm ap_offline_chat_tool python3 tests/test_suite.py
```

See [docs/DOCKER.md](docs/DOCKER.md) for comprehensive Docker documentation.

### Model Selection

The system supports multiple AI models. **Qwen 2.5 (3B) is the default** with 96% accuracy.

```bash
# Use default model (Qwen 2.5)
python main.py

# List available models
python main.py --list-models

# Use specific model
python main.py --model gemma3:4b
python main.py --model ardupilot-stage1  # Legacy model
```

**Available Models:**
- `qwen2.5:3b` (default) - 96% accuracy, 2.5s response
- `gemma3:4b` - 96% accuracy, 4.5s response  
- `ardupilot-stage1` (legacy) - 85% accuracy, 0.4s response

See [Model Selection Guide](docs/MODEL_SELECTION.md) for detailed comparison.

## Usage

### Demo Mode (No Drone Required)

Perfect for testing the AI assistant without hardware:

```bash
python examples/demo.py
```

**Try these commands:**
- "arm the drone"
- "takeoff to 15 meters"
- "check battery status"
- "what is my current position?"
- "land the drone"

### SITL Mode (Simulation)

**Note**: SITL requires ArduPilot installation. See platform-specific guides for setup.

```bash
# Terminal 1: Start ArduPilot SITL
cd ~/ardupilot/ArduCopter
sim_vehicle.py -w --console --map

# Terminal 2: Start AI assistant
cd ap_offline_chat_tool
conda activate ap_chat_tools
python main.py
```

**ArduPilot SITL Setup**:
- Linux: https://ardupilot.org/dev/docs/building-setup-linux.html
- Windows: Use Docker or WSL (see [docs/INSTALL_WINDOWS.md](docs/INSTALL_WINDOWS.md))


# Now you can control the real simulated drone!
```

## 📖 Usage

### Demo Mode

Perfect for testing the AI without setting up SITL:

```bash
python demo.py
```

All drone responses are simulated. Great for:
- Testing natural language commands
- Verifying model accuracy
- Learning available functions
- Quick demonstrations

### SITL Mode

Connect to ArduPilot Software-in-the-Loop simulation:

```bash
# Default connection (UDP 14550)
python main.py

# Custom connection
python main.py -c tcp:127.0.0.1:5760

# With verbose output
python main.py -v

# Use different model
python main.py -m ardupilot-stage2
```

### Available Commands

#### Natural Language Commands

Just speak naturally! The AI understands:

- **Arming/Disarming**: "arm the drone", "disarm motors"
- **Takeoff**: "takeoff to 15 meters", "take off to 20m"
- **Landing**: "land the drone", "land now"
- **Return Home**: "return to launch", "RTL", "go home"
- **Mode Changes**: "change mode to guided", "switch to loiter"
- **Status Checks**: "check battery", "where am I?", "what's my position?"
- **Navigation**: "fly to latitude 28.5, longitude 77.0, altitude 10"

#### Special Commands

- `/help` or `/h` - Show available functions
- `/status` or `/s` - Get drone status (battery, position)
- `/reset` or `/r` - Clear conversation history
- `/quit` or `/q` - Exit application

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Input                          │
│              "arm the drone and takeoff to 15m"             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FunctionGemma Model                       │
│              (ardupilot-stage1, 270M params)                │
│                                                             │
│  Input: Natural language                                    │
│  Output: <start_function_call>call:arm{}<end_function_call> │
│          <start_function_call>call:takeoff{altitude:15}...  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Function Parser                            │
│  Extracts: function_name="arm", arguments={}                │
│           function_name="takeoff", arguments={altitude:15}  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 DroneController (PyMAVLink)                 │
│  Executes: drone.arm() → MAVLink commands                   │
│           drone.takeoff(15) → MAVLink commands              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ArduPilot (SITL or Real Drone)                 │
│  Actions: Motors arm, drone takes off to 15m                │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Stage 1 Functions

### Supported Commands (38 Functions)

**Basic Control:**
- `arm` - Arm drone motors
- `disarm` - Disarm drone motors  
- `takeoff <altitude>` - Takeoff to specified altitude
- `land` - Land at current location
- `rtl` - Return to launch
- `change_mode <mode>` - Change flight mode

**Composite Functions (NEW!):**
- `arm_and_takeoff <altitude>` - Arm and takeoff in one command
- `hover <duration>` - Hold position for X seconds
- `land_and_disarm` - Land and automatically disarm

**Altitude Control:**
- `increase_altitude <meters>` - Climb by specified meters
- `decrease_altitude <meters>` - Descend by specified meters

**Navigation:**
- `goto_location <lat> <lon> <alt>` - Fly to GPS coordinates
- `move_north/south/east/west <meters>` - Directional movement
- `set_yaw <angle>` - Set heading in degrees

**Status & Information:**
- `get_battery` - Battery voltage, current, and percentage
- `get_position` - GPS coordinates and altitude
- `get_mode` - Current flight mode
- `is_armable` - Pre-arm check status

**Parameter Configuration (NEW!):**
- `set_parameter <name> <value>` - Set ArduPilot parameter
- `get_parameter <name>` - Get parameter value

**Mission Planning:**
- `create_mission` - Start new mission
- `add_waypoint <lat> <lon> <alt>` - Add GPS waypoint
- `upload_mission` - Upload to drone
- `start_mission` - Execute mission

**Emergency:**
- `emergency_stop` - Emergency motor stop (USE WITH CAUTION!)

See [Function Library Plan](docs/FUNCTION_LIBRARY_PLAN.md) for complete details.

## ⚙️ Configuration

### Model Selection

```bash
# Use default Stage 1 model
python main.py

# Use custom model
python main.py -m my-custom-model
```

### Connection Strings

```bash
# UDP (default for SITL)
python main.py -c udp:127.0.0.1:14550

# TCP
python main.py -c tcp:127.0.0.1:5760

# Serial
python main.py -c /dev/ttyUSB0

# Serial with baud rate
python main.py -c /dev/ttyUSB0:57600
```

## 🧪 Testing

### Run Demo Mode Test

```bash
python demo.py
# Try: "arm", "takeoff to 10m", "check battery", "where am I?", "land"
```

### Run Unit Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python test_arm.py
python test_movement.py
```

### Verify Model

```bash
# Check if model exists
ollama list | grep ardupilot-stage1

# Test model directly
ollama run ardupilot-stage1 "arm the drone"
```

## 🐛 Troubleshooting

### Model Not Found

```bash
Error: model 'ardupilot-stage1' not found
```

**Solution**: The model needs to be created/imported into Ollama. See [TRAINING_GUIDE.md](docs/TRAINING_GUIDE.md) for instructions.

### Connection Failed

```bash
❌ Failed to connect to drone
```

**Solutions**:
1. Verify SITL is running: `ps aux | grep sim_vehicle`
2. Check connection string matches SITL output
3. Try demo mode first: `python demo.py`

### Import Errors

```bash
ModuleNotFoundError: No module named 'pymavlink'
```

**Solution**: Activate conda environment and install dependencies:
```bash
conda activate ap_chat_tools
pip install -r requirements.txt
```

### Battery/Position Shows "Command executed successfully"

This was a bug in versions before 1.0.0. Update to latest version:
```bash
git pull origin main
```

## 📊 Performance

### Model Metrics

- **Accuracy**: 85% (17/20 test cases)
- **Training Time**: 4 min 24 sec (Colab T4 GPU)
- **Model Size**: 270M parameters
- **Response Time**: < 1 second per command
- **Training Data**: 206 examples (Stage 1)

### Known Limitations

- **Stage 1**: Only 8 functions (core flight operations)
- **Single Commands**: Best with one command at a time
- **English Only**: Trained on English commands
- **Precision**: Coordinates limited to ~6 decimal places

## 🗺️ Roadmap

### Stage 2 (Planned)
- ✅ 15 additional functions (waypoints, missions, advanced navigation)
- ✅ Multi-step command sequences
- ✅ Improved accuracy (target: 90%+)

### Stage 3 (Future)
- ✅ All 29 functions
- ✅ Context awareness
- ✅ Error recovery
- ✅ Multi-language support

## 🛠️ Development

### Project Structure

```
AP_Offline_chat_tools/
├── src/                        # Source code
│   ├── __init__.py
│   ├── drone_functions.py      # PyMAVLink wrapper (29 functions)
│   └── function_gemma.py       # FunctionGemma interface
│
├── examples/                   # Example usage
│   └── demo.py                 # Demo mode (no SITL required)
│
├── tests/                      # Test files
│   ├── __init__.py
│   ├── test_suite.py           # Comprehensive test suite
│   ├── test_arm.py             # Arming tests
│   ├── test_movement.py        # Movement tests
│   └── test_setup.py           # Setup verification
│
├── docs/                       # Documentation
│   └── COMMAND_REFERENCE.md    # Natural language command guide
│
├── scripts/                    # Utility scripts
│   └── setup.sh                # Setup and verification script
│
├── main.py                     # Main entry point (SITL mode)
├── README.md                   # This file
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
├── requirements.txt            # Python dependencies
└── .gitignore                  # Git exclusions
```

### Adding New Functions

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new drone functions
- Improving training data
- Testing requirements
- Code style guidelines

### Command Reference

Having trouble with commands? See [docs/COMMAND_REFERENCE.md](docs/COMMAND_REFERENCE.md) for:
- ✅ Tested phrasings that work
- ❌ Common mistakes to avoid
- 💡 Tips for best results
- 🔧 Troubleshooting guide

**Quick tip:** Use `takeoff to 15 meters` not `takeoff drone at 15`

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Credits

### Technologies Used

- **[ArduPilot](https://ardupilot.org/)** - Open source autopilot software
- **[PyMAVLink](https://github.com/ArduPilot/pymavlink)** - MAVLink protocol library
- **[Google FunctionGemma](https://huggingface.co/google/functiongemma-270m-it)** - Base model for function calling
- **[Ollama](https://ollama.ai/)** - Local model serving
- **[Rich](https://rich.readthedocs.io/)** - Terminal UI library

### Author

**Deepak** - ArduPilot AI Assistant Project

---

**⭐ If you find this project useful, please star it on GitHub!**

**🐛 Found a bug? [Open an issue](../../issues)**

**💡 Have an idea? [Start a discussion](../../discussions)**
