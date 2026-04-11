from backend.deterministic_parser import parse_user_commands


def command_types(text):
    command_like, commands = parse_user_commands(text)
    return command_like, [command["type"] for command in commands], commands


def test_change_mode_to_guided_parses_without_llm():
    command_like, types, commands = command_types("change mode to guided")
    assert command_like is True
    assert types == ["CHANGE_MODE"]
    assert commands[0]["params"]["mode"] == "GUIDED"


def test_arm_drone_parses_without_llm():
    command_like, types, _ = command_types("arm drone")
    assert command_like is True
    assert types == ["ARM"]


def test_takeoff_without_altitude_uses_safe_default():
    command_like, types, commands = command_types("takeoff")
    assert command_like is True
    assert types == ["TAKEOFF"]
    assert commands[0]["params"]["altitude"] == 10


def test_not_changed_is_not_a_command():
    command_like, types, _ = command_types("not changed")
    assert command_like is False
    assert types == []


def test_multi_step_arm_and_takeoff():
    command_like, types, commands = command_types("arm and takeoff to 20m")
    assert command_like is True
    assert types == ["ARM", "TAKEOFF"]
    assert commands[1]["params"]["altitude"] == 20
