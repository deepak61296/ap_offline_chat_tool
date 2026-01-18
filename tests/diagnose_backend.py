"""
Quick diagnostic script to check backend health and identify issues
"""
import requests
import json

BACKEND_URL = "http://localhost:5000"

print("="*60)
print("Backend Diagnostic Tool")
print("="*60)

# Test 1: Health check
print("\n1. Testing /health endpoint...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: Models endpoint
print("\n2. Testing /models endpoint...")
try:
    response = requests.get(f"{BACKEND_URL}/models", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"   Available models: {models}")
    else:
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: Simple chat without telemetry
print("\n3. Testing /chat endpoint (simple)...")
try:
    payload = {
        "message": "hello",
        "mode": "agent",
        "model": "qwen2.5:3b"
    }
    response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data.get('response', '')[:100]}")
    else:
        print(f"   Error: {response.text[:200]}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 4: Chat with telemetry
print("\n4. Testing /chat endpoint (with telemetry)...")
try:
    payload = {
        "message": "arm the drone",
        "mode": "agent",
        "model": "qwen2.5:3b",
        "telemetry": {
            "battery": {"voltage": 12.6, "current": 5.2, "remaining": 85},
            "gps": {"lat": 37.7749, "lon": -122.4194, "alt": 50, "satellites": 12},
            "attitude": {"roll": 0, "pitch": 0, "yaw": 90},
            "speed": {"groundspeed": 0, "airspeed": 0},
            "status": {"mode": "GUIDED", "armed": True}
        }
    }
    response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data.get('response', '')[:100]}")
        print(f"   Command: {data.get('command', {})}")
    else:
        print(f"   Error: {response.text[:500]}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "="*60)
print("Diagnostic complete!")
print("="*60)
print("\nIf you see errors above, check:")
print("1. Backend console for Python errors")
print("2. Ollama is running: ollama list")
print("3. Model is downloaded: ollama pull qwen2.5:3b")
