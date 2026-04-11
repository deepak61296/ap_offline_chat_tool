import importlib


def test_parse_runtime_settings_cli_overrides_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_MODEL", "env-model")
    monkeypatch.setenv("SCRIPT_MODEL", "env-script")
    monkeypatch.setenv("STANDALONE_MODE", "false")

    from backend import config

    settings = config.parse_runtime_settings([
        "--standalone",
        "--model", "cli-model",
        "--script-model", "cli-script",
        "--connect", "udp:127.0.0.1:14551",
    ])

    assert settings.standalone_mode is True
    assert settings.default_model == "cli-model"
    assert settings.script_model == "cli-script"
    assert settings.mavlink_connection == "udp:127.0.0.1:14551"
    assert settings.operation_mode == "standalone"


def test_default_runtime_settings_pick_stable_model(monkeypatch):
    monkeypatch.delenv("DEFAULT_MODEL", raising=False)
    monkeypatch.setenv("SCRIPT_MODEL", "qwen2.5-coder:7b")

    import backend.config as config_module

    config = importlib.reload(config_module)
    assert config.DEFAULT_RUNTIME_SETTINGS.default_model == "qwen2.5:3b"
    assert "qwen2.5:3b" in config.DEFAULT_RUNTIME_SETTINGS.supported_models
