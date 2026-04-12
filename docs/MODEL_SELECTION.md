# Model Selection Guide

The cleaned backend defaults to a single local Ollama model for Agent and Ask mode.

## Default Configuration

- Model: `qwen2.5:3b`
- Size: about 1.9 GB
- Best for: command extraction, telemetry queries, and low-latency local use

## Installation

```bash
ollama pull qwen2.5:3b
ollama list
```

## Changing the Default Model

Edit `backend/config.py`:

```python
DEFAULT_MODEL = "qwen2.5:3b"
OLLAMA_NUM_CTX = 4096
OLLAMA_NUM_GPU = -1
```

After editing, restart the backend:

```bash
python run_server.py
```

## Performance Notes

| Model | Size | RAM Usage | Best For |
|-------|------|-----------|----------|
| qwen2.5:3b | 1.9 GB | 8 GB+ | Default Agent/Ask workflow |

## Troubleshooting

### Model Not Found

```bash
ollama pull qwen2.5:3b
```

### Out of Memory

Reduce context size in `backend/config.py`:

```python
OLLAMA_NUM_CTX = 2048
```

### CPU-Only Mode

Start the backend with:

```bash
python run_server.py --no-gpu
```

## Related Documentation

- [Architecture](ARCHITECTURE.md)
- [Installation Guide](INSTALL_WINDOWS.md)
