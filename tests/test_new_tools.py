"""
Test Suite for New Tools: get_status, get_position, pause, resume, explain_param
Also includes edge case tests for JSON validation and parameter search.

Run with: python -m pytest tests/test_new_tools.py -v
"""

import pytest
import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import (
    TOOL_DEFINITIONS, VALID_TOOLS, validate_and_coerce,
    extract_tool_calls, normalize_tool_call, get_tools_description
)
from backend.param_db import db as param_db


class TestToolDefinitions:
    """Test that all tools are properly defined."""

    def test_all_tools_have_names(self):
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert len(tool["name"]) > 0

    def test_all_tools_have_descriptions(self):
        for tool in TOOL_DEFINITIONS:
            assert "description" in tool
            assert len(tool["description"]) > 10

    def test_valid_tools_matches_definitions(self):
        defined_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert defined_names == VALID_TOOLS

    def test_new_tools_exist(self):
        """Verify new tools are defined."""
        new_tools = ["get_status", "get_position", "pause", "resume", "explain_param"]
        for tool in new_tools:
            assert tool in VALID_TOOLS, f"Missing tool: {tool}"

    def test_tool_count(self):
        """Should have at least 20 tools now."""
        assert len(TOOL_DEFINITIONS) >= 20


class TestValidateAndCoerce:
    """Test JSON validation and type coercion."""

    def test_valid_tool_passes(self):
        result = validate_and_coerce({"tool": "arm"})
        assert result is not None
        assert result["tool"] == "arm"

    def test_invalid_tool_rejected(self):
        result = validate_and_coerce({"tool": "FAKE_COMMAND"})
        assert result is None

    def test_string_to_int_coercion(self):
        result = validate_and_coerce({"tool": "takeoff", "params": {"altitude": "25"}})
        assert result["params"]["altitude"] == 25
        assert isinstance(result["params"]["altitude"], int)

    def test_string_to_float_coercion(self):
        result = validate_and_coerce({"tool": "set_speed", "params": {"speed": "5.5"}})
        assert result["params"]["speed"] == 5.5
        assert isinstance(result["params"]["speed"], float)

    def test_confidence_preserved(self):
        result = validate_and_coerce({"tool": "arm", "confidence": 0.95})
        assert "confidence" in result
        assert result["confidence"] == 0.95

    def test_case_insensitive_tool_name(self):
        result = validate_and_coerce({"tool": "ARM"})
        assert result is not None
        assert result["tool"] == "arm"

    def test_whitespace_stripped(self):
        result = validate_and_coerce({"tool": "  takeoff  ", "params": {"altitude": 20}})
        assert result["tool"] == "takeoff"

    def test_empty_params_handled(self):
        result = validate_and_coerce({"tool": "arm", "params": None})
        assert result["params"] == {}

    def test_string_params_preserved(self):
        result = validate_and_coerce({"tool": "change_mode", "params": {"mode": "LOITER"}})
        assert result["params"]["mode"] == "LOITER"


class TestExtractToolCalls:
    """Test JSON extraction from LLM responses."""

    def test_extract_json_code_block(self):
        response = 'Arming the drone.\n\n```json\n[{"tool":"arm"}]\n```'
        text, calls = extract_tool_calls(response)
        assert len(calls) == 1
        assert calls[0]["tool"] == "arm"
        assert "Arming" in text

    def test_extract_multiple_tools(self):
        response = '```json\n[{"tool":"arm"},{"tool":"takeoff","params":{"altitude":20}}]\n```'
        text, calls = extract_tool_calls(response)
        assert len(calls) == 2
        assert calls[0]["tool"] == "arm"
        assert calls[1]["tool"] == "takeoff"

    def test_invalid_tools_filtered(self):
        response = '```json\n[{"tool":"arm"},{"tool":"INVALID_TOOL"}]\n```'
        text, calls = extract_tool_calls(response)
        assert len(calls) == 1  # INVALID_TOOL should be filtered

    def test_type_coercion_in_extraction(self):
        response = '```json\n[{"tool":"takeoff","params":{"altitude":"30"}}]\n```'
        text, calls = extract_tool_calls(response)
        assert calls[0]["params"]["altitude"] == 30

    def test_raw_json_array_extraction(self):
        response = 'Here you go: [{"tool":"land"}]'
        text, calls = extract_tool_calls(response)
        assert len(calls) == 1
        assert calls[0]["tool"] == "land"

    def test_single_json_object_extraction(self):
        response = 'Okay: {"tool":"rtl"}'
        text, calls = extract_tool_calls(response)
        assert len(calls) == 1
        assert calls[0]["tool"] == "rtl"

    def test_no_json_returns_empty_list(self):
        response = "I don't understand that command."
        text, calls = extract_tool_calls(response)
        assert len(calls) == 0


class TestNormalizeToolCall:
    """Test tool call to command conversion."""

    def test_arm_normalization(self):
        cmd = normalize_tool_call({"tool": "arm", "params": {}})
        assert cmd["type"] == "ARM"

    def test_takeoff_with_altitude(self):
        cmd = normalize_tool_call({"tool": "takeoff", "params": {"altitude": 25}})
        assert cmd["type"] == "TAKEOFF"
        assert cmd["params"]["altitude"] == 25

    def test_move_direction(self):
        cmd = normalize_tool_call({"tool": "move", "params": {"direction": "north", "distance": 10}})
        assert cmd["type"] == "MOVE_DIRECTION"
        assert cmd["params"]["direction"] == "NORTH"

    def test_pause_to_loiter(self):
        """Pause should work (mapped in executor to CHANGE_MODE LOITER)."""
        cmd = normalize_tool_call({"tool": "pause", "params": {}})
        assert cmd["type"] == "PAUSE"

    def test_hold_alias(self):
        """Hold should map to PAUSE."""
        cmd = normalize_tool_call({"tool": "hold", "params": {}})
        assert cmd["type"] == "PAUSE"

    def test_resume_to_auto(self):
        cmd = normalize_tool_call({"tool": "resume", "params": {}})
        assert cmd["type"] == "RESUME"

    def test_get_status(self):
        cmd = normalize_tool_call({"tool": "get_status", "params": {}})
        assert cmd["type"] == "GET_STATUS"

    def test_get_position(self):
        cmd = normalize_tool_call({"tool": "get_position", "params": {}})
        assert cmd["type"] == "GET_POSITION"

    def test_explain_param(self):
        cmd = normalize_tool_call({"tool": "explain_param", "params": {"name": "batt_fs_low_volt"}})
        assert cmd["type"] == "EXPLAIN_PARAM"
        assert cmd["params"]["name"] == "BATT_FS_LOW_VOLT"

    def test_unknown_tool_returns_none(self):
        cmd = normalize_tool_call({"tool": "not_a_real_tool", "params": {}})
        assert cmd is None


class TestParameterDatabase:
    """Test parameter search functionality."""

    def test_database_loaded(self):
        assert len(param_db.params) > 5000

    def test_battery_search(self):
        results = param_db.search("battery failsafe", top_k=3)
        assert len(results) > 0
        # Should return BATT_ params, not BATT2_
        assert any("BATT_" in r["name"] for r in results)

    def test_motor_search(self):
        results = param_db.search("motor spin", top_k=3)
        assert len(results) > 0
        assert any("MOT_" in r["name"] for r in results)

    def test_loiter_search(self):
        results = param_db.search("loiter", top_k=3)
        assert len(results) > 0
        assert any("LOIT_" in r["name"] for r in results)

    def test_compass_search(self):
        results = param_db.search("compass", top_k=3)
        assert len(results) > 0
        assert any("COMPASS_" in r["name"] for r in results)

    def test_exact_param_search(self):
        results = param_db.search("BATT_FS_LOW_VOLT", top_k=1)
        assert len(results) > 0

    def test_sim_params_deprioritized(self):
        """SIM_ parameters should not be top results for real queries."""
        results = param_db.search("battery voltage", top_k=3)
        top_names = [r["name"] for r in results]
        # SIM_BATT_VOLTAGE should not be in top 3
        assert not any(n.startswith("SIM_") for n in top_names)

    def test_no_results_for_nonsense(self):
        results = param_db.search("xyzzy123nonsense", top_k=3)
        assert len(results) == 0


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_empty_tool_name(self):
        result = validate_and_coerce({"tool": ""})
        assert result is None

    def test_none_tool_name(self):
        result = validate_and_coerce({"tool": None})
        assert result is None

    def test_missing_tool_key(self):
        result = validate_and_coerce({"command": "arm"})
        assert result is None

    def test_nested_params(self):
        # Should handle flat params only
        result = validate_and_coerce({
            "tool": "goto",
            "params": {"latitude": 37.7749, "longitude": -122.4194}
        })
        assert result is not None

    def test_malformed_json_in_response(self):
        response = '```json\n{"tool":"arm",,}\n```'
        text, calls = extract_tool_calls(response)
        # Should handle gracefully
        assert isinstance(calls, list)

    def test_very_long_param_value(self):
        result = validate_and_coerce({
            "tool": "search_param",
            "params": {"query": "a" * 1000}
        })
        assert result is not None


class TestToolsDescription:
    """Test the tools description generator."""

    def test_description_not_empty(self):
        desc = get_tools_description()
        assert len(desc) > 100

    def test_all_tools_in_description(self):
        desc = get_tools_description()
        for tool in VALID_TOOLS:
            assert tool in desc

    def test_description_format(self):
        desc = get_tools_description()
        # Should have proper format with dashes
        assert "  - " in desc


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
