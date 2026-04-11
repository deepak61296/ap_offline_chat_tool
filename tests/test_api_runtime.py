from types import SimpleNamespace

from backend.api_server import create_app
from backend.config import RuntimeSettings


class FakeTelemetry:
    def to_dict(self):
        return {
            "battery": {"voltage": 12.4, "current": 4.1, "remaining": 82},
            "gps": {"latitude": 1.23, "longitude": 4.56, "altitude": 12.0, "satellites": 10, "fix_type": "3D"},
            "attitude": {"yaw": 90},
            "status": {"mode": "GUIDED", "armed": True},
        }


class FakeMavlinkManager:
    def __init__(self):
        self.connected = True
        self.telemetry = FakeTelemetry()
        self.state = SimpleNamespace(value="connected")
        self.connection_string = "udp:127.0.0.1:14550"

    def execute_command(self, command):
        return SimpleNamespace(success=True, message=f"{command['type']} ok", data=None)


class DisconnectedMavlinkManager:
    connected = False
    state = SimpleNamespace(value="error")
    connection_string = ""


class ConnectedSparseTelemetryManager:
    def __init__(self):
        self.connected = True
        self.state = SimpleNamespace(value="connected")
        self.connection_string = "tcp:127.0.0.1:5760"
        self.telemetry = SimpleNamespace(
            to_dict=lambda: {
                "battery": {"voltage": 0, "current": 0, "remaining": 0},
                "gps": {"satellites": 0, "fix_type": "NO_FIX"},
                "status": {"mode": "UNKNOWN", "armed": False},
            }
        )


def test_status_exposes_runtime_metadata(monkeypatch):
    settings = RuntimeSettings(
        standalone_mode=True,
        default_model="qwen2.5:3b",
        script_model="qwen2.5-coder:7b",
        supported_models=["qwen2.5:3b", "qwen2.5-coder:7b"],
    )
    app = create_app(settings)
    app.config["MAVLINK_MANAGER"] = FakeMavlinkManager()

    from backend import api_server

    monkeypatch.setattr(
        api_server,
        "ollama",
        SimpleNamespace(list=lambda: {"models": [{"name": "qwen2.5:3b"}]}),
    )

    client = app.test_client()
    response = client.get("/status")
    data = response.get_json()

    assert response.status_code == 200
    assert data["operation_mode"] == "standalone"
    assert data["default_model"] == "qwen2.5:3b"
    assert data["runtime"]["operation_mode"] == "standalone"
    assert data["mavlink"]["telemetry_health"] == "healthy"
    assert data["mavlink"]["connection_string"] == "udp:127.0.0.1:14550"
    assert data["mavlink"]["configured_connection_string"] == ""


def test_chat_injects_backend_telemetry_in_standalone(monkeypatch):
    settings = RuntimeSettings(
        standalone_mode=True,
        default_model="qwen2.5:3b",
        script_model="qwen2.5-coder:7b",
        supported_models=["qwen2.5:3b", "qwen2.5-coder:7b"],
    )
    app = create_app(settings)
    app.config["MAVLINK_MANAGER"] = FakeMavlinkManager()

    captured = {}

    def fake_plan(**kwargs):
        captured["plan_telemetry"] = kwargs["telemetry"]
        return "Executing.", [{"type": "ARM", "params": {}}]

    def fake_execute(**kwargs):
        captured["execute_telemetry"] = kwargs["telemetry"]
        captured["standalone_mode"] = kwargs["standalone_mode"]
        return SimpleNamespace(
            ai_response="Plan executed",
            command=None,
            commands=None,
            plan_summary="ARM: OK",
            tasks_executed=1,
            tasks_total=1,
            execution_attempted=True,
            execution_success=True,
            execution_error=None,
            step_results=[{"command": "ARM", "success": True, "message": "ok"}],
        )

    monkeypatch.setattr("backend.api_server.planner_plan", fake_plan)
    monkeypatch.setattr("backend.api_server.executor_execute", fake_execute)

    client = app.test_client()
    response = client.post("/chat", json={"message": "arm the drone", "mode": "agent"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["operation_mode"] == "standalone"
    assert data["command"] is None
    assert captured["execute_telemetry"]["status"]["mode"] == "GUIDED"
    assert captured["execute_telemetry"]["gps"]["latitude"] == 1.23
    assert captured["standalone_mode"] is True


def test_command_like_prompt_fails_closed_when_llm_returns_no_tools(monkeypatch):
    settings = RuntimeSettings(standalone_mode=False, default_model="qwen2.5:3b")
    app = create_app(settings)

    monkeypatch.setattr(
        "backend.api_server.planner_plan",
        lambda **kwargs: ("Changing mode to AUTO.", []),
    )

    client = app.test_client()
    response = client.post("/chat", json={"message": "go into weird flight posture", "mode": "agent"})
    data = response.get_json()

    assert response.status_code == 400
    assert data["success"] is False
    assert data["interaction_type"] == "command"
    assert data["parse_source"] == "none"
    assert data["execution_attempted"] is False
    assert data["execution_error"] == "No structured command was produced"


def test_standalone_disconnected_rejects_deterministic_command():
    settings = RuntimeSettings(standalone_mode=True, default_model="qwen2.5:3b")
    app = create_app(settings)
    app.config["MAVLINK_MANAGER"] = DisconnectedMavlinkManager()

    client = app.test_client()
    response = client.post("/chat", json={"message": "change mode to guided", "mode": "agent"})
    data = response.get_json()

    assert response.status_code == 400
    assert data["success"] is False
    assert data["interaction_type"] == "command"
    assert data["parse_source"] == "deterministic"
    assert data["execution_success"] is False
    assert data["execution_error"] == "MAVLink is not connected"


def test_standalone_connected_executes_deterministic_command():
    settings = RuntimeSettings(standalone_mode=True, default_model="qwen2.5:3b")
    app = create_app(settings)
    app.config["MAVLINK_MANAGER"] = FakeMavlinkManager()

    client = app.test_client()
    response = client.post("/chat", json={"message": "change mode to guided", "mode": "agent"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["parse_source"] == "deterministic"
    assert data["execution_attempted"] is True
    assert data["execution_success"] is True
    assert data["step_results"][0]["command"] == "CHANGE_MODE"


def test_agent_hi_uses_canned_conversation_without_llm(monkeypatch):
    settings = RuntimeSettings(standalone_mode=True, default_model="qwen2.5:3b")
    app = create_app(settings)
    app.config["MAVLINK_MANAGER"] = DisconnectedMavlinkManager()

    def fail_plan(**kwargs):
        raise AssertionError("planner should not run for simple greeting")

    monkeypatch.setattr("backend.api_server.planner_plan", fail_plan)

    client = app.test_client()
    response = client.post("/chat", json={"message": "hi", "mode": "agent"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["interaction_type"] == "conversation"
    assert data["parse_source"] == "deterministic"
    assert "Hi." in data["response"]


def test_agent_help_uses_canned_response_without_llm(monkeypatch):
    settings = RuntimeSettings(standalone_mode=True, default_model="qwen2.5:3b")
    app = create_app(settings)
    app.config["MAVLINK_MANAGER"] = DisconnectedMavlinkManager()

    def fail_plan(**kwargs):
        raise AssertionError("planner should not run for help")

    monkeypatch.setattr("backend.api_server.planner_plan", fail_plan)

    client = app.test_client()
    response = client.post("/chat", json={"message": "?", "mode": "agent"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["interaction_type"] == "conversation"
    assert "Agent commands" in data["response"]


def test_standalone_connected_with_sparse_telemetry_reports_transport_connected(monkeypatch):
    settings = RuntimeSettings(standalone_mode=True, default_model="qwen2.5:3b")
    app = create_app(settings)
    app.config["MAVLINK_MANAGER"] = ConnectedSparseTelemetryManager()

    def fail_plan(**kwargs):
        raise AssertionError("planner should not run for help")

    monkeypatch.setattr("backend.api_server.planner_plan", fail_plan)

    client = app.test_client()
    response = client.post("/chat", json={"message": "?", "mode": "agent"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["connection_state"] == "connected"
    assert "CONNECTED to drone" in data["response"]
