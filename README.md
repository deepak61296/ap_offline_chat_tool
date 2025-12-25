# 🚁 ArduPilot AI Assistant

![Stage 1 Complete](https://img.shields.io/badge/Stage%201-Complete-success)
![Model Accuracy](https://img.shields.io/badge/Accuracy-85%25-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

> **Natural language drone control - 100% offline, no API keys required**

An offline AI assistant that translates natural language commands into ArduPilot drone control actions using a fine-tuned Google FunctionGemma model (270M parameters). Control your drone by simply talking to it!

## ✨ Key Features

- 🤖 **Natural Language Control**: "arm the drone and takeoff to 15 meters"
- 🔒 **100% Offline**: No internet, no API keys, runs entirely on your laptop
- ⚡ **Fast & Lightweight**: 270M parameter model, instant responses
- 🎯 **85% Accuracy**: Fine-tuned on ArduPilot-specific commands
- 🛡️ **Safety First**: Built-in pre-flight checks and safety validations
- 🎮 **Two Modes**: Demo mode (no drone needed) and SITL mode (full simulation)

## 🎬 Demo

```bash
$ python demo.py

╔═══════════════════════════════════════════════════════════╗
║     🚁 ArduPilot AI Assistant - Stage 1 (85% Accuracy)    ║
║        Natural language drone control - Fully offline!    ║
╚═══════════════════════════════════════════════════════════╝

You: arm the drone and takeoff to 15 meters
✅ Parsed: arm({})
✈️ Drone armed (simulated)
🤖 Assistant: Drone armed successfully

✅ Parsed: takeoff({'altitude': 15})
🚁 Taking off to 15m (simulated)
🤖 Assistant: Taking off to 15m

You: check battery status
✅ Parsed: get_battery({})
🤖 Assistant: 🔋 Battery: 12.60V, 8.50A, 87% remaining

You: where am I?
✅ Parsed: get_position({})
🤖 Assistant: 📍 Position: Lat 28.535500°, Lon 77.391000°, Alt 0.0m, Heading 90.0°
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Conda** (recommended for environment management)
- **Ollama** (for running the model locally)
- **ArduPilot SITL** (optional, for full simulation)

### Installation

```bash
# 1. Clone the repository
cd /path/to/your/projects
git clone <your-repo-url>
cd AP_Offline_chat_tools

# 2. Run the setup script
bash setup.sh

# 3. Verify installation
python demo.py
```

That's it! You should see the demo mode welcome screen.

### First Flight (Demo Mode)

```bash
# Start demo mode (no drone/SITL needed)
python demo.py

# Try these commands:
# - "arm the drone"
# - "takeoff to 10 meters"
# - "check battery"
# - "where am I?"
# - "land"
```

### First Flight (SITL Mode)

```bash
# Terminal 1: Start ArduPilot SITL
cd ~/ardupilot/ArduCopter
sim_vehicle.py -w --console --map

# Terminal 2: Start the AI assistant
cd /path/to/AP_Offline_chat_tools
conda activate ap_chat_tools
python main.py

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

The current model (Stage 1) supports 8 core functions:

| Function | Description | Example Command |
|----------|-------------|-----------------|
| `arm()` | Arm drone motors | "arm the drone" |
| `disarm()` | Disarm drone motors | "disarm" |
| `takeoff(altitude)` | Takeoff to specified altitude | "takeoff to 15 meters" |
| `land()` | Land at current location | "land the drone" |
| `rtl()` | Return to launch position | "return home" |
| `change_mode(mode)` | Change flight mode | "change mode to guided" |
| `get_battery()` | Get battery status | "check battery" |
| `get_position()` | Get current position | "where am I?" |

**Note**: 21 additional functions are available in `drone_functions.py` and will be included in Stage 2 training.

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
