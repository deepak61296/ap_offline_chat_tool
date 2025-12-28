# Full Docker Container with ArduPilot SITL

This Docker container includes **everything** you need:
- ArduPilot SITL (Software In The Loop)
- MAVProxy
- Ollama with ardupilot-stage1 model
- ArduPilot AI Assistant
- All dependencies

## Quick Start

### Option 1: Demo Mode (No SITL)

```bash
# Build the image
docker build -f Dockerfile.full -t ardupilot-ai-full .

# Run demo mode
docker run -it --rm ardupilot-ai-full demo
```

### Option 2: SITL Mode (Full Simulation)

```bash
# Run with SITL
docker run -it --rm --privileged --network host ardupilot-ai-full sitl
```

This will:
1. Start Ollama and download the model
2. Start ArduPilot SITL (ArduCopter)
3. Start the AI Assistant connected to SITL

### Option 3: Run Tests

```bash
docker run --rm ardupilot-ai-full test
```

### Option 4: Interactive Shell

```bash
docker run -it --rm ardupilot-ai-full bash
```

## Using Docker Compose

### Demo Mode

```bash
docker compose --profile demo up
```

### SITL Mode

```bash
docker compose --profile sitl up
```

### Test Mode

```bash
docker compose --profile test up
```

## What's Included

### Software
- **Ubuntu 22.04** - Base OS
- **Python 3.10** - Runtime
- **ArduPilot** - Latest Copter-4.5 branch
- **MAVProxy** - Ground control station
- **Ollama** - AI model runtime
- **ardupilot-stage1** - Fine-tuned model (auto-downloaded)

### Ports Exposed
- `8080` - Future web interface
- `14550` - MAVLink UDP (default SITL)
- `14551` - MAVLink UDP (secondary)
- `5760` - MAVLink TCP
- `5761` - MAVLink TCP (secondary)

## Build Details

### Build Time
- **First build**: ~15-20 minutes (downloads ArduPilot, builds SITL)
- **Subsequent builds**: ~2-3 minutes (cached layers)

### Image Size
- **Final image**: ~3-4 GB
  - Ubuntu base: ~200 MB
  - ArduPilot + dependencies: ~2 GB
  - Ollama: ~500 MB
  - Model (downloaded at runtime): ~550 MB

## Usage Examples

### 1. Quick Demo Test

```bash
docker run -it --rm ardupilot-ai-full demo

# Try commands:
# - arm the drone
# - takeoff 20
# - check battery
```

### 2. Full SITL Simulation

```bash
# Terminal 1: Run container with SITL
docker run -it --rm --privileged --network host ardupilot-ai-full sitl

# The AI assistant will connect to SITL automatically
# Try real commands:
# - arm the drone
# - takeoff to 15 meters
# - check battery
# - where am I?
```

### 3. Development Mode

```bash
# Get a shell
docker run -it --rm ardupilot-ai-full bash

# Inside container:
sim_vehicle.py -w --console --map  # Start SITL manually
python3 main.py                     # Start AI assistant
```

### 4. With Persistent Data

```bash
# Create volumes
docker volume create ollama-models
docker volume create sitl-data

# Run with persistence
docker run -it --rm \
  -v ollama-models:/home/ardupilot/.ollama \
  -v sitl-data:/home/ardupilot/ardupilot \
  --privileged --network host \
  ardupilot-ai-full sitl
```

## Modes Explained

### Demo Mode (`demo`)
- **What**: AI assistant with simulated drone responses
- **Use**: Test the AI without SITL
- **Network**: Not required
- **Time**: Instant startup

### SITL Mode (`sitl`)
- **What**: Full ArduPilot simulation + AI assistant
- **Use**: Test with real ArduPilot SITL
- **Network**: `--network host` required
- **Time**: ~30 seconds startup (SITL initialization)

### Test Mode (`test`)
- **What**: Runs all test suites
- **Use**: Verify everything works
- **Network**: Not required
- **Time**: ~10 seconds

### Bash Mode (`bash`)
- **What**: Interactive shell
- **Use**: Development, debugging, manual testing
- **Network**: Optional
- **Time**: Instant

## Troubleshooting

### SITL Won't Start

```bash
# Check SITL logs
docker run -it --rm ardupilot-ai-full bash
tail -f /tmp/sitl.log
```

### Model Download Slow

First run downloads 552MB model. Be patient or use persistent volume:

```bash
docker volume create ollama-models
docker run -v ollama-models:/home/ardupilot/.ollama ...
```

### Connection Issues

SITL mode requires `--network host` and `--privileged`:

```bash
docker run -it --rm --privileged --network host ardupilot-ai-full sitl
```

### Build Fails

```bash
# Clean build
docker build --no-cache -f Dockerfile.full -t ardupilot-ai-full .
```

## Comparison: Light vs Full Container

### Light Container (`Dockerfile`)
- **Size**: ~1.5 GB
- **Build time**: ~5 minutes
- **Includes**: Ollama + AI Assistant
- **Use case**: Demo mode only

### Full Container (`Dockerfile.full`)
- **Size**: ~3-4 GB
- **Build time**: ~15-20 minutes
- **Includes**: ArduPilot SITL + MAVProxy + Ollama + AI Assistant
- **Use case**: Full simulation + demo

## Advanced Usage

### Custom SITL Parameters

```bash
docker run -it --rm --privileged --network host ardupilot-ai-full bash

# Inside container:
cd /home/ardupilot/ardupilot/ArduCopter
sim_vehicle.py --console --map --aircraft test --speedup 2
```

### Connect External GCS

```bash
# Run SITL in container
docker run -it --rm --privileged --network host ardupilot-ai-full sitl

# On host, connect Mission Planner/QGroundControl to:
# UDP: localhost:14550
# TCP: localhost:5760
```

### Multiple Vehicles

```bash
# Vehicle 1
docker run -it --rm --privileged --network host \
  ardupilot-ai-full bash -c "sim_vehicle.py --instance 0"

# Vehicle 2
docker run -it --rm --privileged --network host \
  ardupilot-ai-full bash -c "sim_vehicle.py --instance 1"
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Docker Test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -f Dockerfile.full -t ardupilot-ai-full .
      
      - name: Run tests
        run: docker run --rm ardupilot-ai-full test
```

## Production Deployment

For production, use the full container with persistent volumes:

```bash
docker run -d \
  --name ardupilot-sitl \
  --restart unless-stopped \
  --privileged \
  --network host \
  -v ollama-models:/home/ardupilot/.ollama \
  -v sitl-data:/home/ardupilot/ardupilot \
  ardupilot-ai-full sitl
```

---

**Need help?** See [DOCKER.md](DOCKER.md) for the light container or open an issue.
