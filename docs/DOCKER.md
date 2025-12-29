# Docker Setup for ArduPilot AI Assistant

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and run
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Using Docker Directly

```bash
# Build image
docker build -t ap_offline_chat_tool .

# Run demo mode
docker run -it --rm ap_offline_chat_tool

# Run with custom command
docker run -it --rm ap_offline_chat_tool python3 tests/test_suite.py
```

## What's Included

The Docker container includes:
- Ubuntu 22.04
- Python 3.10
- Ollama (latest)
- All Python dependencies
- ArduPilot AI Assistant code
- ardupilot-stage1 model (created from Modelfile)

## Container Details

### Base Image
- `ubuntu:22.04`

### Installed Software
- Python 3.10
- Ollama
- pymavlink
- rich
- ollama Python package

### User
- Non-root user: `ardupilot` (UID 1000)
- Home directory: `/home/ardupilot`

### Working Directory
- `/app`

### Volumes
- `ollama-models`: Persistent storage for Ollama models

## Testing the Container

### Run Test Suite

```bash
# Run all tests
docker-compose run --rm ardupilot-assistant python3 tests/test_suite.py

# Run preprocessing tests
docker-compose run --rm ardupilot-assistant python3 tests/test_preprocessing.py

# Run setup verification
docker-compose run --rm ardupilot-assistant python3 tests/test_setup.py
```

### Interactive Demo Mode

```bash
# Start interactive demo
docker-compose run --rm ardupilot-assistant python3 examples/demo.py
```

### Verify Installation

```bash
# Check Python version
docker-compose run --rm ardupilot-assistant python3 --version

# Check Ollama
docker-compose run --rm ardupilot-assistant ollama list

# Check model
docker-compose run --rm ardupilot-assistant ollama show ardupilot-stage1
```

## Building from Scratch

```bash
# Clean build (no cache)
docker-compose build --no-cache

# Build with specific tag
docker build -t ap_offline_chat_tool:v1.0.1 .
```

## Troubleshooting

### Model Not Found

If the model isn't created automatically:

```bash
# Enter container
docker-compose run --rm ardupilot-assistant bash

# Inside container, create model
cd /app/models
ollama serve &
sleep 5
ollama create ardupilot-stage1 -f ardupilot-stage1.Modelfile
```

### Ollama Not Starting

```bash
# Check Ollama logs
docker-compose logs ardupilot-assistant

# Restart service
docker-compose restart
```

### Permission Issues

The container runs as non-root user `ardupilot`. If you encounter permission issues:

```bash
# Run as root (not recommended for production)
docker-compose run --rm --user root ardupilot-assistant bash
```

## Resource Requirements

### Minimum
- CPU: 1 core
- RAM: 2 GB
- Disk: 2 GB

### Recommended
- CPU: 2+ cores
- RAM: 4 GB
- Disk: 5 GB

## Environment Variables

You can customize the container with environment variables:

```yaml
# In docker-compose.yml
environment:
  - PYTHONUNBUFFERED=1
  - OLLAMA_HOST=http://localhost:11434
  - MODEL_NAME=ardupilot-stage1
```

## Development Mode

To develop inside the container:

```yaml
# Uncomment in docker-compose.yml
volumes:
  - ./src:/app/src
  - ./examples:/app/examples
  - ./tests:/app/tests
```

Then:

```bash
docker-compose up -d
docker-compose exec ardupilot-assistant bash
```

## Production Deployment

For production use:

1. **Build optimized image:**
   ```bash
   docker build -t ap_offline_chat_tool:prod .
   ```

2. **Run with resource limits:**
   ```bash
   docker run -d \
     --name ardupilot-assistant \
     --memory="4g" \
     --cpus="2.0" \
     --restart=unless-stopped \
     ap_offline_chat_tool:prod
   ```

3. **Use docker-compose with limits** (already configured)

## Security Notes

- Container runs as non-root user (`ardupilot`)
- No personal information included
- No credentials or API keys
- Model is created from Modelfile (no external dependencies)

## Cleaning Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes model data)
docker-compose down -v

# Remove images
docker rmi ap_offline_chat_tool:latest

# Clean all Docker resources
docker system prune -a
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t ap_offline_chat_tool .
      
      - name: Run tests
        run: docker run ap_offline_chat_tool python3 tests/test_suite.py
```

## Multi-Architecture Support

To build for multiple architectures:

```bash
# Enable buildx
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ap_offline_chat_tool:latest \
  --push .
```

---

**Need help?** See the main [README.md](README.md) or open an issue.
