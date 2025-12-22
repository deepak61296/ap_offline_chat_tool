# ArduPilot AI Assistant

AI-powered chat assistant for ArduPilot Mission Planner. Control your drone with natural language and get answers from official documentation.

## Quick Start

```bash
# 1. Install Ollama
# Download from: https://ollama.com

# 2. Pull a model
ollama pull qwen2.5:3b

# 3. Start the backend
cd ap_offline_chat_tool
scripts\start_backend.bat

# 4. Open Mission Planner and press Ctrl+L
```

## Features

- **Two Modes:**
  - **Agent Mode**: Execute drone commands (ARM, TAKEOFF, LAND, etc.)
  - **Ask Mode**: Get answers from 8,000+ ArduPilot documentation chunks

- **RAG System**: Retrieves relevant documentation for accurate answers
- **Offline**: No internet required, runs locally
- **Safe**: Commands only execute in Agent mode
- **Cancel Button**: Stop long AI responses anytime
- **CPU Support**: Works on systems without GPU

## Supported Models

- **qwen2.5:3b** (recommended) - Fast, accurate, works on most systems
- **gemma3:4b** - Slightly better quality, needs more RAM

More models coming soon!

## Installation

### Requirements
- Python 3.8+
- Ollama
- Mission Planner (for drone control)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/deepak61296/ap_offline_chat_tool.git
cd ap_offline_chat_tool

# 2. Create conda environment
conda create -n ap_chat_tools python=3.10 -y
conda activate ap_chat_tools

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Install Ollama and pull model
ollama pull qwen2.5:3b

# 5. Start backend
scripts\start_backend.bat
```

### CPU-Only Mode

If you don't have a GPU or want to save power:

```bash
scripts\start_backend_cpu.bat        # CPU only
scripts\start_backend_lowpower.bat   # CPU + reduced context
```

## Usage

### In Mission Planner

1. Launch Mission Planner
2. Press **Ctrl+L** to open AI Chat
3. Select mode (Agent or Ask)
4. Start chatting!

**Example Commands (Agent Mode):**
- "arm the drone"
- "takeoff to 15 meters"
- "move north 20 meters"
- "increase altitude by 10m"
- "land"

**Example Questions (Ask Mode):**
- "how do I calibrate my compass?"
- "what is the WPNAV_SPEED parameter?"
- "how to setup a geofence?"

### Cancel Long Responses

While AI is thinking, the Send button becomes a red Cancel button. Click it to stop processing.

## Project Structure

```
ap_offline_chat_tool/
├── backend/              # Core AI backend
│   ├── api_server.py    # HTTP API
│   ├── commands.py      # Command extraction
│   ├── prompts.py       # AI prompts
│   ├── rag.py           # Documentation retrieval
│   └── config.py        # Settings
│
├── scripts/             # Startup scripts
│   ├── start_backend.bat
│   ├── start_backend_cpu.bat
│   └── start_backend_lowpower.bat
│
├── docs/                # Documentation
└── tests/               # Tests
```

## Configuration

Edit `backend/config.py` to change:
- API host/port (default: `127.0.0.1:5000`)
- Default model
- Context window size
- RAG settings

## TODO

### In Progress
- [ ] QGroundControl integration
- [ ] More drone commands (waypoints, missions)
- [ ] Full hardware testing

### Planned
- [ ] MAVProxy plugin
- [ ] Streaming responses
- [ ] Multi-language support
- [ ] Fine-tuned ArduPilot model
- [ ] Voice control
- [ ] Flight log analysis

### Completed
- [x] Mission Planner integration
- [x] RAG system with 8K+ docs
- [x] Cancel button
- [x] CPU/GPU modes
- [x] Altitude change commands

## Troubleshooting

**Backend won't start:**
- Make sure Ollama is running: `ollama list`
- Check if model is downloaded: `ollama pull qwen2.5:3b`
- Verify conda environment: `conda activate ap_chat_tools`

**Mission Planner can't connect:**
- Check backend is running on port 5000
- Look for "AI Backend connected ✓" in chat

**AI gives wrong answers:**
- Switch to Ask mode for documentation-based answers
- Try a different model: `gemma3:4b`

## Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file

## Credits

- **ArduPilot** - Open source autopilot
- **Ollama** - Local AI model serving
- **ChromaDB** - Vector database for RAG
- **Mission Planner** - Ground control station

---

**Made with ❤️ for the ArduPilot community**

**Questions?** Open an issue on GitHub
