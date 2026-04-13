# Project Overview

This repo contains a local Flask backend that converts natural-language drone requests into structured command objects for ArduPilot integrations.

## What is in scope

- HTTP API in `backend/api_server.py`
- planner/executor pipeline in `backend/planner.py` and `backend/executor.py`
- structured tool definitions in `backend/tools.py`
- parameter lookup in `backend/param_db.py`
- optional direct MAVLink execution in `backend/mavlink_manager.py`
- integration copies under `integrations/mission_planner/`, `integrations/mavproxy/`, and `integrations/qgroundcontrol/`

## Default runtime

- backend version: `3.0.0`
- server: Flask
- default model: `qwen2.5:3b`
- default API bind: `0.0.0.0:5000`
- default operation mode: `integrated`

## Supported interaction modes

- `ask`: read-only answers using telemetry context
- `agent`: model emits JSON tool calls; backend normalizes and executes/plans commands

## What the backend returns

For `POST /chat` the backend returns text plus structured command data. Depending on the request:

- conversational or informational request: `command` is `null`
- single executable action: `command` contains one command
- multi-step action: `command` is the first queued command and `commands` may contain the full sequence

## Current design constraints

- only `qwen2.5:3b` is listed in `SUPPORTED_MODELS`
- standalone features depend on `pymavlink`
- parameter search is local keyword ranking over `apm.pdef.json`
- training code exists in `training/` but is not part of the request path
