# Model Selection Guide

The backend uses qwen2.5-coder models via Ollama for local LLM inference.

### Default Configuration

**Agent/Ask Modes:**
- Model: `qwen2.5-coder:3b`
- Size: 1.9 GB
- Speed: Fast (1-2s responses)
- Best for: Command extraction and telemetry queries

**Script Mode:**
- Model: `qwen2.5-coder:7b`
- Size: 4.7 GB
- Speed: Medium (2-4s responses)
- Best for: Lua script generation

### Installation

```bash
# Install both recommended models
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b

# Verify installation
ollama list
```

## Supported Models

Only **qwen2.5-coder** models are currently supported:

**qwen2.5-coder:3b** (Default for Agent/Ask modes)
- Size: 1.9 GB
- Speed: Fast (1-2s)
- Recommended for command extraction

**qwen2.5-coder:7b** (Default for Script mode)
- Size: 4.7 GB
- Speed: Medium (2-4s)
- Recommended for Lua script generation

## Changing Models

### Method 1: Edit Configuration File

Edit `backend/config.py`:

```python
# Agent and Ask modes
DEFAULT_MODEL = "qwen2.5-coder:3b"  # Change to your preferred model

# Script mode
SCRIPT_MODEL = "qwen2.5-coder:7b"   # Change to your preferred model

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_NUM_CTX = 4096              # Context window size
OLLAMA_NUM_GPU = -1                # -1 for auto, 0 for CPU only
```

After editing, restart the backend:
```bash
# Stop backend (Ctrl+C)
# Start again
conda activate ardupilot_ai
python -m backend.api_server
```

### Method 2: Command Line Flags

Currently not supported. Edit config.py instead.

## Performance Comparison

| Model | Size | RAM Usage | Speed | Best For |
|-------|------|-----------|-------|----------|
| qwen2.5-coder:3b | 1.9 GB | 8 GB | Fast (1-2s) | Agent/Ask modes |
| qwen2.5-coder:7b | 4.7 GB | 12 GB | Medium (2-4s) | Script generation |

Speed ratings based on typical CPU inference time.

## GPU Acceleration

If you have an NVIDIA GPU with CUDA support, Ollama will automatically use it for 2-3x speedup.

**Check GPU usage:**
```bash
# While backend is running
nvidia-smi

# Look for ollama process using GPU memory
```

**Force CPU-only mode:**

Edit `backend/config.py`:
```python
OLLAMA_NUM_GPU = 0  # Disable GPU
```

Or start backend with flag:
```bash
python -m backend.api_server --no-gpu
```

## System Requirements

| Model | Min RAM | Recommended RAM | GPU VRAM (optional) |
|-------|---------|-----------------|---------------------|
| qwen2.5-coder:3b | 8 GB | 12 GB | 4 GB |
| qwen2.5-coder:7b | 12 GB | 16 GB | 8 GB |

## Troubleshooting

### Model Not Found

```bash
# Error: Model 'qwen2.5-coder:3b' not found
# Solution: Pull the model
ollama pull qwen2.5-coder:3b
```

### Out of Memory

```bash
# Error: OOM or system freezes
# Solution: Reduce context window in backend/config.py
OLLAMA_NUM_CTX = 2048  # Default is 4096
```

### Slow Responses

```bash
# Solution 1: Use GPU if available (automatic if CUDA installed)
# Solution 2: Reduce context window in backend/config.py
OLLAMA_NUM_CTX = 2048
```

## Model Testing

Test a model before committing:

```bash
# Start Ollama
ollama serve

# Test model directly
ollama run qwen2.5-coder:3b "Extract command: arm the drone"

# Should respond with something like:
# "Arming the drone now."
```

Then verify with backend:
```bash
# Start backend
conda activate ardupilot_ai
python -m backend.api_server

# Test via API
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "arm the drone", "mode": "agent"}'
```

## Best Practices

1. Use `qwen2.5-coder:3b` for Agent/Ask modes (fast command extraction)
2. Use `qwen2.5-coder:7b` for Script mode (better code generation)
3. Always test in simulation (SITL) before real hardware

## Related Documentation

- [Architecture](ARCHITECTURE.md) - How models integrate with backend
- [Installation Guide](INSTALL_WINDOWS.md) - Setup instructions
