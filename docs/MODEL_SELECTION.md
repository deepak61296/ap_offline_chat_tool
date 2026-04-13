# Model Selection

Current server defaults come from `backend/config.py`.

## Default

- `DEFAULT_MODEL = "qwen2.5:3b"`
- `SUPPORTED_MODELS = ["qwen2.5:3b"]`
- `OLLAMA_NUM_CTX = 4096`, or `2048` with `--low-power`
- `OLLAMA_NUM_GPU = -1`, or `0` with `--no-gpu`

## How the model is chosen

- if `POST /chat` includes `model`, that value is passed to `ollama.chat()`
- otherwise the backend uses `DEFAULT_MODEL`

The code does not currently enforce that the request model is inside `SUPPORTED_MODELS`.

## Install the default model

```bash
ollama pull qwen2.5:3b
ollama list
```

## Change defaults

Edit `backend/config.py` and restart the server.
