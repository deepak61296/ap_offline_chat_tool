# Contributing

## Backend entrypoints

- `run_server.py`: process entrypoint
- `backend/api_server.py`: Flask routes and mode dispatch
- `backend/prompts.py`: ask/agent prompt templates
- `backend/planner.py`: LLM call for agent mode
- `backend/tools.py`: tool schema, JSON extraction, normalization
- `backend/executor.py`: command planning and special flows
- `backend/commands.py`: validation and legacy regex helpers

## Add or change a command

For planner/executor behavior, update these layers together:

1. Add or change the tool in `backend/tools.py`
2. Update prompt examples/rules in `backend/prompts.py`
3. Ensure `normalize_tool_call()` maps the tool to the correct command struct
4. Add validation in `backend/commands.py:validate_command()` if needed
5. Add executor handling in `backend/executor.py` if the command is backend-only or needs special behavior
6. Update the integration side if command execution format changed
7. Update tests under `tests/`

## Integration copies

Files under `integrations/` are repo-local copies of client-side integration code:

- `integrations/mission_planner/AIBackendService.cs`
- `integrations/mission_planner/DroneCommandExecutor.cs`
- `integrations/mavproxy/mavproxy_ai_backend.py`

If the backend response contract changes, update those copies in the same change.

## Test commands

Typical local checks:

```bash
python3 -m pytest tests/test_new_tools.py -v
python3 -m pytest tests/test_comprehensive.py -v
```

`tests/test_agentic_pipeline.py` is an HTTP-level test and expects the backend server to already be running.
