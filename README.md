# ArduPilot AI Backend

AI-powered chat assistant for ArduPilot Mission Planner. Control your copter with natural language commands and get answers from official ArduPilot documentation.

## ⚠️ Important Notes

- **Mission Planner Compatibility:** This backend **only works** with this Mission Planner fork: https://github.com/deepak61296/MissionPlanner
- **Vehicle Support:** Currently supports **Copter only** (Plane and Rover support coming soon)
- **License:** GPL-3.0 (same as ArduPilot)

## Features

- **Agent Mode:** Execute drone commands (ARM, TAKEOFF, LAND, move, altitude changes, etc.)
- **Ask Mode:** Get answers from 8,000+ ArduPilot documentation chunks using RAG
- **Offline:** Runs completely locally, no internet required
- **Small Model:** Uses qwen2.5:3b (only 2GB) via Ollama
- **Safe:** Commands only execute in Agent mode with explicit user input

## Test Results

**Comprehensive Test Suite:** 151 tests covering commands, natural language, edge cases, and safety

- **Pass Rate:** 76.8% (116/151 tests passing)
- **Model:** qwen2.5:3b (3 billion parameters)
- **Note:** This is excellent accuracy considering the rigorous test suite on such a small model

See `tests/test_report.html` for detailed results.

## Quick Start

### 1. Install Ollama

Download and install Ollama from https://ollama.com

### 2. Pull the Model

```bash
ollama pull qwen2.5:3b
```

### 3. Setup Python Environment

```bash
# Clone this repo
git clone https://github.com/deepak61296/ArduPilot-AI-Backend.git
cd ArduPilot-AI-Backend/ap_offline_chat_tool

# Create conda environment
conda create -n ap_chat_tools python=3.10 -y
conda activate ap_chat_tools

# Install dependencies
pip install -r backend/requirements.txt
```

### 4. Start the Backend

```bash
# Windows
scripts\start_backend.bat

# Linux/Mac
python backend/api_server.py
```

The backend will start on `http://localhost:5000`

### 5. Use with Mission Planner

1. Download and install the compatible Mission Planner fork: https://github.com/deepak61296/MissionPlanner
2. Launch Mission Planner
3. Press **Ctrl+L** to open AI Chat
4. Start chatting!

## Usage Examples

### Agent Mode (Command Execution)

```
"arm the drone"
"takeoff to 15 meters"
"move north 20 meters"
"increase altitude by 10m"
"change mode to loiter"
"land"
```

### Ask Mode (Documentation Q&A)

```
"how do I calibrate my compass?"
"what is the WPNAV_SPEED parameter?"
"how to setup a geofence?"
"explain RTL mode"
```

## Alternative Startup Scripts

```bash
# CPU only (no GPU)
scripts\start_backend_cpu.bat

# Low power mode (reduced context window)
scripts\start_backend_lowpower.bat
```

## Configuration

Edit `backend/config.py` to change:
- API host/port (default: `127.0.0.1:5000`)
- Model selection
- Context window size
- RAG settings
- Maximum altitude/distance limits

## Project Structure

```
ap_offline_chat_tool/
├── backend/
│   ├── api_server.py       # HTTP API server
│   ├── commands.py         # Command extraction logic
│   ├── prompts.py          # AI prompts for Agent/Ask modes
│   ├── rag.py              # RAG system for documentation
│   └── config.py           # Configuration settings
├── scripts/
│   ├── start_backend.bat   # Main startup script
│   ├── start_backend_cpu.bat
│   └── start_backend_lowpower.bat
├── tests/
│   ├── test_comprehensive.py   # Main test suite (170+ tests)
│   └── test_report.html        # Latest test results
└── docs/                   # Documentation
```

## Running Tests

```bash
# Run comprehensive test suite
python tests/test_comprehensive.py

# Or use the batch file
scripts\run_comprehensive_tests.bat

# View results
# Open tests/test_report.html in browser
```

## Troubleshooting

**Backend won't start:**
- Verify Ollama is running: `ollama list`
- Check model is downloaded: `ollama pull qwen2.5:3b`
- Activate conda environment: `conda activate ap_chat_tools`

**Mission Planner can't connect:**
- Ensure backend is running on port 5000
- Check firewall isn't blocking localhost:5000
- Look for "AI Backend connected ✓" message in chat

**Commands not executing:**
- Make sure you're in Agent mode (not Ask mode)
- Use direct commands: "arm the drone" not "can you arm?"
- Check backend logs for errors

## Development

### Adding New Commands

1. Add command example to `backend/prompts.py`
2. Add extraction logic to `backend/commands.py`
3. Add test cases to `tests/test_comprehensive.py`
4. Run tests to verify

### Fine-Tuning the Model

See `fine_tuning/` directory for scripts to fine-tune qwen2.5:3b on ArduPilot-specific commands (coming soon).

## Roadmap

- [ ] Fine-tuned ArduPilot model (90%+ test accuracy)
- [ ] Plane and Rover support
- [ ] QGroundControl integration
- [ ] MAVProxy plugin
- [ ] Waypoint and mission commands
- [ ] Voice control
- [ ] Flight log analysis

## Contributing

Contributions welcome! This project follows ArduPilot's GPL-3 license.

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

GPL-3.0 - See LICENSE file

This project is licensed under GPL-3 to maintain compatibility with ArduPilot.

## Credits

- **ArduPilot** - Open source autopilot (https://ardupilot.org)
- **Ollama** - Local AI model serving (https://ollama.com)
- **ChromaDB** - Vector database for RAG
- **Mission Planner** - Ground control station

---

**Made for the ArduPilot community**

**Questions or Issues?** Open an issue on GitHub
