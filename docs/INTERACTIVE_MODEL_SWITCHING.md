# Interactive Model Switching

## Overview

This document explains how to change AI models at runtime without restarting the backend server.

## Current Implementation

**Status:** Not currently supported via command-line interface.

To switch models, you must:
1. Stop the backend server (Ctrl+C)
2. Edit `backend/config.py`
3. Restart the backend server

## Configuration File Method

Edit `backend/config.py`:

```python
# Agent and Ask modes
DEFAULT_MODEL = "qwen2.5-coder:3b"  # Change this

# Script mode
SCRIPT_MODEL = "qwen2.5-coder:7b"   # Change this
```

Restart backend:
```bash
# Terminal with backend running: Ctrl+C to stop
conda activate ardupilot_ai
python -m backend.api_server
```

## Available Models

See [MODEL_SELECTION.md](MODEL_SELECTION.md) for full list of supported models.

**Quick reference:**
- `qwen2.5-coder:1.5b` - Smallest, fastest
- `qwen2.5-coder:3b` - Default, balanced
- `qwen2.5-coder:7b` - Best for scripts
- `qwen2.5-coder:14b` - Largest, most accurate

## Per-Mode Configuration

The backend supports different models for different modes:

**Agent/Ask Mode Model:**
```python
DEFAULT_MODEL = "qwen2.5-coder:3b"
```

**Script Mode Model:**
```python
SCRIPT_MODEL = "qwen2.5-coder:7b"
```

This allows using a faster model for command extraction and a more powerful model for code generation.

## Verifying Model Change

After restarting with new model:

```bash
curl http://localhost:5000/health
```

Check response for current model name.

## Future Enhancement

**Planned:** Runtime model switching via API endpoint or command-line flag.

Example (not yet implemented):
```bash
# Future API (not available yet)
curl -X POST http://localhost:5000/config \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-coder:7b"}'
```

## Related Documentation

- [MODEL_SELECTION.md](MODEL_SELECTION.md) - Choosing models
- [MODEL_COMPARISON.md](MODEL_COMPARISON.md) - Performance benchmarks
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
