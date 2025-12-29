# Docker Troubleshooting - URL Scheme Error

## Error
```
docker.errors.DockerException: Error while fetching server API version: 
Not supported URL scheme http+docker
```

## Cause
This is a compatibility issue between old `docker-compose` (v1.29.2) and newer Python `requests` library.

## Solutions

### Solution 1: Use Docker Directly (Recommended)

Instead of `docker-compose`, use `docker` commands directly:

```bash
# Build image
docker build -t ap_offline_chat_tool .

# Run demo mode (interactive)
docker run -it --rm ap_offline_chat_tool

# Run tests
docker run --rm ap_offline_chat_tool python3 tests/test_suite.py

# Run with Ollama service
docker run -it --rm \
  --network host \
  -v ollama-models:/home/ardupilot/.ollama \
  ap_offline_chat_tool
```

### Solution 2: Upgrade docker-compose

```bash
# Remove old docker-compose
sudo apt remove docker-compose

# Install Docker Compose V2 (plugin)
sudo apt update
sudo apt install docker-compose-v2

# Verify
docker compose version
```

Then use `docker compose` (with space) instead of `docker-compose`:

```bash
docker compose up --build
docker compose run --rm ardupilot-assistant python3 examples/demo.py
```

### Solution 3: Fix Python Package Conflict

```bash
# Upgrade requests in system Python
pip3 install --upgrade requests urllib3

# Or downgrade docker-compose
pip3 install docker-compose==1.25.0
```

## Quick Test

Try building with docker directly:

```bash
cd /home/deepak/Documents/Projects/AP_Offline_chat_tools
docker build -t ap_offline_chat_tool .
```

If this works, use the Docker commands from Solution 1.

---

**Recommended**: Use Solution 1 (Docker directly) - it's simpler and more reliable.
