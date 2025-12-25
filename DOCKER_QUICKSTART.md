# Docker Quick Start

## Running the Container

```bash
# Run interactive demo (recommended)
docker run -it --rm ardupilot-ai-assistant
```

**First run:** Takes ~1-2 minutes (downloads 552MB model from Ollama)  
**Subsequent runs:** Instant (model is cached in volume)

## What Happens

1. **Container starts** - Shows setup progress
2. **Ollama service starts** - Background service
3. **Model downloads** - Pulls `deepakpopli/ardupilot-stage1` from Ollama
4. **Demo starts** - Interactive prompt appears

## Try These Commands

Once the demo starts, try:
- `arm the drone`
- `takeoff 20`
- `check battery`
- `where am I?`
- `land the drone`
- `/quit` to exit

## Persistent Model Storage

To keep the model between runs:

```bash
# Create a volume for model storage
docker volume create ollama-models

# Run with persistent storage
docker run -it --rm \
  -v ollama-models:/home/ardupilot/.ollama \
  ardupilot-ai-assistant
```

Now the model only downloads once!

## Running Tests

```bash
# Run full test suite
docker run --rm ardupilot-ai-assistant python3 tests/test_suite.py

# Run preprocessing tests
docker run --rm ardupilot-ai-assistant python3 tests/test_preprocessing.py
```

## Troubleshooting

**Slow first run?**
- Model download is 552MB, be patient
- Subsequent runs are instant with volume

**Connection errors?**
- Wait for "Setup complete!" message
- Ollama needs ~10 seconds to start

**Want to rebuild?**
```bash
docker build --no-cache -t ardupilot-ai-assistant .
```

---

For full documentation, see [docs/DOCKER.md](../docs/DOCKER.md)
