# Model Selection Guide

This guide explains how to choose and configure LLM models for the ArduPilot AI Backend.

## Recommended Models

The backend uses Ollama for local LLM inference. Different models work better for different tasks:

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

## Alternative Models

### Smaller Models (Lower Resource Requirements)

**qwen2.5-coder:1.5b**
- Size: 1.0 GB
- Speed: Very fast (<1s)
- Accuracy: Good for simple commands
- Use case: Low-power systems, quick testing

```bash
ollama pull qwen2.5-coder:1.5b
```

**llama3.2:3b**
- Size: 2.0 GB
- Speed: Fast (1-2s)
- Accuracy: Good general performance
- Use case: Alternative to qwen for variety

```bash
ollama pull llama3.2:3b
```

### Larger Models (Better Accuracy)

**qwen2.5-coder:14b**
- Size: 9.0 GB
- Speed: Slow (4-8s)
- Accuracy: Excellent
- Use case: Complex script generation, high accuracy needs

```bash
ollama pull qwen2.5-coder:14b
```

**llama3.1:8b**
- Size: 4.7 GB
- Speed: Medium (2-4s)
- Accuracy: Very good
- Use case: Better natural language understanding

```bash
ollama pull llama3.1:8b
```

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

| Model | Size | RAM Usage | Speed | Accuracy | Best For |
|-------|------|-----------|-------|----------|----------|
| qwen2.5-coder:1.5b | 1.0 GB | 3 GB | ★★★★★ | ★★★☆☆ | Low-power systems |
| qwen2.5-coder:3b | 1.9 GB | 5 GB | ★★★★☆ | ★★★★☆ | Default choice |
| llama3.2:3b | 2.0 GB | 5 GB | ★★★★☆ | ★★★★☆ | Alternative |
| qwen2.5-coder:7b | 4.7 GB | 10 GB | ★★★☆☆ | ★★★★★ | Script generation |
| llama3.1:8b | 4.7 GB | 10 GB | ★★★☆☆ | ★★★★★ | Complex queries |
| qwen2.5-coder:14b | 9.0 GB | 16 GB | ★★☆☆☆ | ★★★★★ | Maximum accuracy |

Speed ratings based on typical inference time (CPU mode).

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

## System Requirements by Model

| Model | Min RAM | Recommended RAM | GPU VRAM (optional) |
|-------|---------|-----------------|---------------------|
| 1.5b | 4 GB | 8 GB | 2 GB |
| 3b | 8 GB | 12 GB | 4 GB |
| 7b | 12 GB | 16 GB | 8 GB |
| 14b | 16 GB | 24 GB | 16 GB |

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
# Solution 1: Use smaller model
ollama pull qwen2.5-coder:1.5b

# Solution 2: Reduce context window in backend/config.py
OLLAMA_NUM_CTX = 2048  # Default is 4096
```

### Slow Responses

```bash
# Solution 1: Use GPU if available
# (Automatic, just ensure CUDA is installed)

# Solution 2: Use smaller model
ollama pull qwen2.5-coder:1.5b

# Solution 3: Reduce context window
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

1. **Development:** Use `qwen2.5-coder:3b` for fast iteration
2. **Production:** Use `qwen2.5-coder:7b` for better accuracy
3. **Low-power:** Use `qwen2.5-coder:1.5b` for constrained systems
4. **Testing:** Always test model changes with full test suite

## Related Documentation

- [Model Comparison](MODEL_COMPARISON.md) - Benchmark results
- [Architecture](ARCHITECTURE.md) - How models integrate with backend
- [Configuration](../backend/config.py) - Full configuration options
