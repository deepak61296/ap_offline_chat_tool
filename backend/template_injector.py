"""
Template Injection System
Detects user intent and injects the appropriate template with correct APIs
"""

import re


# Template library with CORRECT APIs
TEMPLATES = {
    "battery_voltage_monitor": """-- Monitor battery voltage and warn if below {threshold}V

function update()
    -- Safety check: only run when armed
    if not arming:is_armed() then
        return update, 1000
    end

    local voltage = battery:voltage(0)

    if voltage and voltage < {threshold} then
        gcs:send_text(4, string.format("Low battery: %.2fV", voltage))
    end

    return update, 5000
end

return update()""",

    "gps_satellite_monitor": """-- Monitor GPS satellites and warn if below {min_sats}

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local num_sats = gps:num_sats(0)

    if num_sats and num_sats < {min_sats} then
        gcs:send_text(4, string.format("Low GPS: %d sats", num_sats))
    end

    return update, 2000
end

return update()""",

    "altitude_monitor": """-- Monitor altitude and warn if exceeds {max_alt}m

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local position = ahrs:get_position()
    if position then
        local altitude = position:alt() / 100  -- Convert cm to meters
        if altitude > {max_alt} then
            gcs:send_text(4, string.format("High altitude: %.1fm", altitude))
        end
    end

    return update, 2000
end

return update()""",

    "auto_rtl_battery": """-- Auto RTL when battery below {threshold}%

local RTL_MODE = 6
local triggered = false

function update()
    if not arming:is_armed() then
        triggered = false
        return update, 1000
    end

    if vehicle:get_mode() == RTL_MODE then
        return update, 1000
    end

    local remaining = battery:capacity_remaining_pct(0)

    if remaining and remaining < {threshold} and not triggered then
        gcs:send_text(3, string.format("Auto-RTL: Battery %.0f%%", remaining))
        vehicle:set_mode(RTL_MODE)
        triggered = true
    end

    return update, 2000
end

return update()""",

    "battery_temp_arming_check": """-- Arming check: Battery temperature must be below {max_temp}°C

local auth_id = assert(arming:get_aux_auth_id())
local MAX_TEMP = {max_temp}

function update()
    if not auth_id then
        return update, 5000
    end

    local temp = battery:get_temperature(0)

    if not temp then
        arming:set_aux_auth_failed(auth_id, "Could not read battery temperature")
    elseif temp >= MAX_TEMP then
        arming:set_aux_auth_failed(auth_id, string.format("Battery temp too high: %.1fC", temp))
    else
        arming:set_aux_auth_passed(auth_id)
    end

    return update, 5000
end

return update()""",

    "battery_resistance_check": """-- Arming check: Battery internal resistance must be below {max_resistance} Ohms

local auth_id = assert(arming:get_aux_auth_id())
local MAX_RESISTANCE = {max_resistance}

function update()
    if not auth_id then
        return update, 5000
    end

    local num_batts = battery:num_instances()
    local all_ok = true

    for i = 0, num_batts - 1 do
        local resistance = battery:get_resistance(i)
        if resistance and resistance > MAX_RESISTANCE then
            local msg = string.format("Batt[%d] high resistance: %.3f Ohms", i + 1, resistance)
            arming:set_aux_auth_failed(auth_id, msg)
            gcs:send_text(3, msg)
            all_ok = false
            break
        end
    end

    if all_ok then
        arming:set_aux_auth_passed(auth_id)
    end

    return update, 500
end

return update()""",

    "attitude_monitor": """-- Monitor attitude (roll, pitch, yaw) and rotation rates

function update()
    -- Get attitude in radians, convert to degrees
    local roll = math.deg(ahrs:get_roll_rad())
    local pitch = math.deg(ahrs:get_pitch_rad())
    local yaw = math.deg(ahrs:get_yaw_rad())

    -- Get rotation rates
    local rates = ahrs:get_gyro()
    if rates then
        local roll_rate = math.deg(rates:x())
        local pitch_rate = math.deg(rates:y())
        local yaw_rate = math.deg(rates:z())

        gcs:send_text(6, string.format("Att: R%.1f P%.1f Y%.1f | Rate: R%.1f P%.1f Y%.1f",
            roll, pitch, yaw, roll_rate, pitch_rate, yaw_rate))
    end

    return update, 1000
end

return update()""",

    "parameter_reader": """-- Read {param_name} parameter and display via GCS

function update()
    local value = param:get("{param_name}")

    if value then
        gcs:send_text(6, string.format("{param_name} = %.1f", value))
    else
        gcs:send_text(4, "Could not read {param_name}")
    end

    return update, 10000
end

return update()""",
}


# Intent detection patterns
INTENT_PATTERNS = {
    "battery_voltage_monitor": [
        r'battery.*voltage.*monitor',
        r'monitor.*battery.*voltage',
        r'battery.*warn.*\d+\.?\d*v',
        r'warn.*battery.*below',
    ],
    "gps_satellite_monitor": [
        r'gps.*satellite',
        r'monitor.*gps',
        r'satellite.*count',
        r'gps.*warn.*\d+',
    ],
    "altitude_monitor": [
        r'altitude.*exceed',
        r'altitude.*warning',
        r'altitude.*\d+',
        r'warn.*altitude',
    ],
    "auto_rtl_battery": [
        r'auto.*rtl.*battery',
        r'rtl.*battery.*\d+',
        r'trigger.*rtl.*battery',
        r'battery.*rtl',
    ],
    "battery_temp_arming_check": [
        r'arming.*check.*battery.*temp',
        r'prevent.*arming.*temp',
        r'battery.*temp.*arming',
    ],
    "battery_resistance_check": [
        r'arming.*check.*resistance',
        r'resistance.*arming',
        r'internal.*resistance',
    ],
    "attitude_monitor": [
        r'attitude.*roll.*pitch.*yaw',
        r'monitor.*attitude.*rotation',
        r'roll.*pitch.*yaw.*rate',
    ],
    "parameter_reader": [
        r'read.*parameter',
        r'parameter.*display',
        r'show.*parameter',
    ],
}


def detect_intent(user_request: str) -> str:
    """Detect which template best matches user's request"""

    user_lower = user_request.lower()

    # Score each template
    scores = {}
    for template_name, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, user_lower):
                score += 1
        if score > 0:
            scores[template_name] = score

    # Return best match
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]

    return None


def extract_parameters(user_request: str, template_name: str) -> dict:
    """Extract parameters from user request"""

    params = {}

    # Battery voltage threshold
    if "battery" in template_name and "voltage" in template_name:
        match = re.search(r'(\d+\.?\d*)\s*v', user_request, re.IGNORECASE)
        params["threshold"] = match.group(1) if match else "11.5"

    # GPS satellites
    if "gps" in template_name or "satellite" in template_name:
        match = re.search(r'(\d+)\s*sat', user_request, re.IGNORECASE)
        params["min_sats"] = match.group(1) if match else "6"

    # Altitude
    if "altitude" in template_name:
        match = re.search(r'(\d+)\s*m', user_request, re.IGNORECASE)
        params["max_alt"] = match.group(1) if match else "100"

    # Battery percentage for RTL
    if "rtl" in template_name and "battery" in template_name:
        match = re.search(r'(\d+)%', user_request)
        params["threshold"] = match.group(1) if match else "20"

    # Temperature
    if "temp" in template_name:
        match = re.search(r'(\d+)\s*[°c]', user_request, re.IGNORECASE)
        params["max_temp"] = match.group(1) if match else "45"

    # Resistance
    if "resistance" in template_name:
        match = re.search(r'(\d+\.?\d*)\s*ohm', user_request, re.IGNORECASE)
        params["max_resistance"] = match.group(1) if match else "0.03"

    # Parameter name
    if "parameter" in template_name:
        match = re.search(r'([A-Z_]+)', user_request)
        params["param_name"] = match.group(1) if match else "WPNAV_SPEED"

    return params


def generate_from_template(user_request: str) -> tuple:
    """
    Generate Lua script from template if pattern matches

    Returns:
        (lua_code, template_used) or (None, None) if no template matches
    """

    # Detect intent
    template_name = detect_intent(user_request)

    if not template_name or template_name not in TEMPLATES:
        return None, None

    # Get template
    template = TEMPLATES[template_name]

    # Extract parameters
    params = extract_parameters(user_request, template_name)

    # Fill template
    lua_code = template
    for key, value in params.items():
        lua_code = lua_code.replace(f"{{{key}}}", str(value))

    return lua_code, template_name


# Test the system
if __name__ == "__main__":
    test_requests = [
        "Monitor battery voltage and warn if below 11.5V",
        "Create script to monitor GPS satellites and warn if below 6",
        "Automatically trigger RTL when battery drops below 20%",
        "Create an arming check that prevents arming if battery temperature exceeds 45°C",
        "Monitor attitude (roll, pitch, yaw) and rotation rates",
    ]

    print("Template Injection Test")
    print("=" * 70)

    for request in test_requests:
        print(f"\nRequest: {request}")
        code, template = generate_from_template(request)

        if code:
            print(f"✓ Template: {template}")
            print(f"  Code length: {len(code)} chars")
        else:
            print("✗ No template match - will use LLM")

    print("\n" + "=" * 70)
