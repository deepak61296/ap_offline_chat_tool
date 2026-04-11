#!/bin/bash
# start_agent.sh
# Launches the ArduPilot AI Backend in True Standalone Mode
# and opens the interactive Agent CLI interface.

set -u

SERVER_PID=""
BACKEND_URL="http://127.0.0.1:5000"
BACKEND_LOG="agent_server.log"

cleanup() {
    if [ -n "${SERVER_PID}" ] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        echo
        echo "Cleaning up backend server (PID ${SERVER_PID})..."
        kill "${SERVER_PID}" 2>/dev/null || true
        wait "${SERVER_PID}" 2>/dev/null || true
    fi
}

port_5000_in_use() {
    ss -ltn 2>/dev/null | grep -Eq '[:.]5000[[:space:]]'
}

stop_existing_local_processes() {
    pkill -f "conda run --no-capture-output -n ardupilot_ai python run_server.py" 2>/dev/null || true
    pkill -f "python run_server.py" 2>/dev/null || true
    pkill -f "python agent.py" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "=========================================="
echo "    ArduPilot AI - True Standalone Agent  "
echo "=========================================="

echo "[1/3] Cleaning up old processes..."
stop_existing_local_processes
sleep 1

if port_5000_in_use; then
    echo "Port 5000 is still in use after cleanup. Refusing to attach to an unknown backend."
    exit 1
fi

echo "[2/3] Starting AI Backend (API Server)..."
# SITL/MAVProxy commonly forwards telemetry to 14550. The backend will
# also try tcp:127.0.0.1:5760 and udp:127.0.0.1:14550 if this misses.
conda run --no-capture-output -n ardupilot_ai python run_server.py --standalone --connect udp:127.0.0.1:14551 > "${BACKEND_LOG}" 2>&1 &
SERVER_PID=$!

echo "      Waiting for server to initialize..."
READY=0
STATUS_JSON=""
MAX_WAIT_SECONDS=45
for _ in $(seq 1 "${MAX_WAIT_SECONDS}"); do
    if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
        echo "Backend process exited during startup."
        tail -n 80 "${BACKEND_LOG}" 2>/dev/null || true
        exit 1
    fi

    STATUS_JSON="$(curl -fsS "${BACKEND_URL}/status" 2>/dev/null || true)"
    if [ -n "${STATUS_JSON}" ] && echo "${STATUS_JSON}" | grep -q '"operation_mode"[[:space:]]*:[[:space:]]*"standalone"'; then
        READY=1
        break
    fi
    sleep 1
done

if [ "${READY}" -ne 1 ]; then
    echo "Backend did not become ready on ${BACKEND_URL} within ${MAX_WAIT_SECONDS}s."
    tail -n 80 "${BACKEND_LOG}" 2>/dev/null || true
    exit 1
fi

echo "      Backend status:"
echo "${STATUS_JSON}"
echo

echo "[3/3] Launching Interactive Copilot CLI..."
conda run --no-capture-output -n ardupilot_ai python agent.py

echo "Goodbye!"
