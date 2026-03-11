"""Post-processing fixes for LLM-generated ArduPilot Lua scripts."""

import re


# ArduPilot mode numbers
MODE_MAP = {
    # Common modes
    '"RTL"': '6',
    "'RTL'": '6',
    '"LAND"': '9',
    "'LAND'": '9',
    '"GUIDED"': '4',
    "'GUIDED'": '4',
    '"AUTO"': '3',
    "'AUTO'": '3',
    '"LOITER"': '5',
    "'LOITER'": '5',
    '"STABILIZE"': '0',
    "'STABILIZE'": '0',
    '"ALT_HOLD"': '2',
    "'ALT_HOLD'": '2',
    '"BRAKE"': '17',
    "'BRAKE'": '17',

    # Case variations
    '"Rtl"': '6',
    '"rtl"': '6',
    '"Land"': '9',
    '"land"': '9',
    '"Guided"': '4',
    '"guided"': '4',
}


def fix_mode_strings_to_numbers(code: str) -> str:
    """
    Fix vehicle:set_mode("RTL") -> vehicle:set_mode(6)
    ArduPilot uses numeric mode values, not strings
    """
    for string_mode, number_mode in MODE_MAP.items():
        # Fix vehicle:set_mode("RTL") -> vehicle:set_mode(6)
        code = code.replace(f'vehicle:set_mode({string_mode})', f'vehicle:set_mode({number_mode})')

    return code


def fix_common_api_mistakes(code: str) -> str:
    """
    Fix common API name mistakes the LLM makes
    """

    # Battery API fixes
    fixes = {
        # Common battery mistakes
        r'battery:get_voltage\(': 'battery:voltage(',
        r'battery:get_current\(': 'battery:current_amps(',
        r'battery:get_remaining\(': 'battery:capacity_remaining_pct(',
        r'battery:get_capacity_remaining\(': 'battery:capacity_remaining_pct(',
        r'battery:remaining\(': 'battery:capacity_remaining_pct(',

        # GPS mistakes (ahrs vs gps confusion)
        r'ahrs:num_sats\(': 'gps:num_sats(',
        r'ahrs:satellites\(': 'gps:num_sats(',

        # Altitude mistakes
        r'ahrs:get_relative_altitude\(': 'ahrs:get_hagl(',
        r'ahrs:altitude\(': 'ahrs:get_hagl(',

        # Attitude mistakes (missing _rad suffix)
        r'ahrs:roll\(': 'ahrs:get_roll_rad(',
        r'ahrs:pitch\(': 'ahrs:get_pitch_rad(',
        r'ahrs:yaw\(': 'ahrs:get_yaw_rad(',
        r'ahrs:get_roll\(': 'ahrs:get_roll_rad(',  # Missing _rad
        r'ahrs:get_pitch\(': 'ahrs:get_pitch_rad(',
        r'ahrs:get_yaw\(': 'ahrs:get_yaw_rad(',

        # Mode mistakes
        r'vehicle:mode\(': 'vehicle:get_mode(',

        # Arming mistakes
        r'arming:armed\(': 'arming:is_armed(',

        # Parameter mistakes
        r'param:read\(': 'param:get(',
        r'param:write\(': 'param:set(',
    }

    for wrong, correct in fixes.items():
        code = re.sub(wrong, correct, code)

    return code


def ensure_instance_parameters(code: str) -> str:
    """
    Ensure battery/GPS/sensor calls have instance parameter (usually 0)
    """

    # Patterns that need instance parameter
    patterns = [
        # battery:voltage() -> battery:voltage(0)
        (r'battery:voltage\(\s*\)', 'battery:voltage(0)'),
        (r'battery:current_amps\(\s*\)', 'battery:current_amps(0)'),
        (r'battery:capacity_remaining_pct\(\s*\)', 'battery:capacity_remaining_pct(0)'),
        (r'battery:get_temperature\(\s*\)', 'battery:get_temperature(0)'),
        (r'battery:get_resistance\(\s*\)', 'battery:get_resistance(0)'),

        # gps:num_sats() -> gps:num_sats(0)
        (r'gps:num_sats\(\s*\)', 'gps:num_sats(0)'),
        (r'gps:status\(\s*\)', 'gps:status(0)'),
        (r'gps:location\(\s*\)', 'gps:location(0)'),
    ]

    for pattern, replacement in patterns:
        code = re.sub(pattern, replacement, code)

    return code


def add_safety_checks(code: str) -> str:
    """
    Add common safety checks if missing
    (Optional - only for basic scripts)
    """

    # Check if arming check is missing in update function
    if 'function update()' in code and 'arming:is_armed()' not in code:
        # Don't add for arming checks themselves
        if 'arming:get_aux_auth_id' not in code:
            # Add safety check after function update()
            code = code.replace(
                'function update()',
                'function update()\n    -- Safety check: only run when armed\n    if not arming:is_armed() then\n        return update, 1000\n    end'
            )

    return code


def clean_formatting(code: str) -> str:
    """
    Clean up formatting issues
    """

    # Remove excessive blank lines (more than 2 in a row)
    code = re.sub(r'\n{3,}', '\n\n', code)

    # Ensure consistent indentation (2 or 4 spaces)
    # This is tricky, so we'll leave it simple

    return code


def postprocess_lua_script(code: str, aggressive: bool = False) -> tuple:
    """
    Main post-processing function

    Args:
        code: The generated Lua script
        aggressive: If True, adds safety checks and other enhancements

    Returns:
        (processed_code, fixes_applied)
    """

    original_code = code
    fixes_applied = []

    # 1. Fix mode strings to numbers (CRITICAL)
    old_code = code
    code = fix_mode_strings_to_numbers(code)
    if code != old_code:
        fixes_applied.append("mode_strings_to_numbers")

    # 2. Fix common API mistakes
    old_code = code
    code = fix_common_api_mistakes(code)
    if code != old_code:
        fixes_applied.append("api_name_fixes")

    # 3. Ensure instance parameters
    old_code = code
    code = ensure_instance_parameters(code)
    if code != old_code:
        fixes_applied.append("instance_parameters")

    # 4. Add safety checks (only if aggressive)
    if aggressive:
        old_code = code
        code = add_safety_checks(code)
        if code != old_code:
            fixes_applied.append("safety_checks")

    # 5. Clean formatting
    code = clean_formatting(code)

    return code, fixes_applied


def test_postprocessor():
    """Test the post-processor with common mistakes"""

    test_cases = [
        # Test 1: Mode string
        ('vehicle:set_mode("RTL")', 'vehicle:set_mode(6)'),

        # Test 2: Battery API
        ('battery:get_voltage()', 'battery:voltage(0)'),

        # Test 3: GPS confusion
        ('ahrs:num_sats()', 'gps:num_sats(0)'),

        # Test 4: Attitude
        ('ahrs:roll()', 'ahrs:get_roll_rad('),

        # Test 5: Instance parameter
        ('battery:voltage()', 'battery:voltage(0)'),
    ]

    print("Testing Post-Processor")
    print("=" * 60)

    for i, (wrong, expected) in enumerate(test_cases, 1):
        processed, fixes = postprocess_lua_script(wrong)
        success = expected in processed
        status = "✓" if success else "✗"
        print(f"{status} Test {i}: {wrong} -> {processed.strip()}")
        if fixes:
            print(f"   Fixes applied: {', '.join(fixes)}")

    print("=" * 60)


if __name__ == "__main__":
    test_postprocessor()

    # Example usage
    print("\n\nExample: Full Script")
    print("=" * 60)

    example_code = '''
function update()
    if vehicle:get_mode() == "RTL" then
        return update, 1000
    end

    local voltage = battery:get_voltage()
    local sats = ahrs:num_sats()

    if voltage < 11.5 then
        vehicle:set_mode("RTL")
    end

    return update, 5000
end
return update()
'''

    print("BEFORE:")
    print(example_code)

    processed, fixes = postprocess_lua_script(example_code)

    print("\nAFTER:")
    print(processed)

    print(f"\nFixes applied: {', '.join(fixes) if fixes else 'None'}")
