"""Lua template library for common ArduPilot scripting patterns."""

import re


TEMPLATES = {
    # === BASIC MONITORING ===

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

    "rangefinder_monitor": """-- Monitor rangefinder distance and warn if below {min_distance}m

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local distance = rangefinder:distance_cm(0)

    if distance then
        local distance_m = distance / 100  -- Convert cm to meters
        if distance_m < {min_distance} then
            gcs:send_text(4, string.format("Low rangefinder: %.1fm", distance_m))
        end
    end

    return update, 1000
end

return update()""",

    # === AUTONOMOUS ACTIONS ===

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

    "auto_land_altitude": """-- Auto LAND when altitude below {min_altitude}m

local LAND_MODE = 9
local triggered = false

function update()
    if not arming:is_armed() then
        triggered = false
        return update, 1000
    end

    if vehicle:get_mode() == LAND_MODE then
        return update, 1000
    end

    local position = ahrs:get_position()
    if position then
        local altitude = position:alt() / 100  -- Convert cm to meters
        if altitude < {min_altitude} and not triggered then
            gcs:send_text(3, string.format("Auto-LAND: Altitude %.1fm", altitude))
            vehicle:set_mode(LAND_MODE)
            triggered = true
        end
    end

    return update, 1000
end

return update()""",

    # === ARMING CHECKS ===

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

    "gps_arming_check": """-- Arming check: GPS must have at least {min_sats} satellites

local auth_id = assert(arming:get_aux_auth_id())
local MIN_SATS = {min_sats}

function update()
    if not auth_id then
        return update, 5000
    end

    local num_sats = gps:num_sats(0)

    if not num_sats then
        arming:set_aux_auth_failed(auth_id, "Could not read GPS")
    elseif num_sats < MIN_SATS then
        arming:set_aux_auth_failed(auth_id, string.format("GPS: only %d sats (need %d)", num_sats, MIN_SATS))
    else
        arming:set_aux_auth_passed(auth_id)
    end

    return update, 2000
end

return update()""",

    # === ATTITUDE & NAVIGATION ===

    "attitude_monitor": """-- Monitor attitude (roll, pitch, yaw) and rotation rates

function update()
    -- Get attitude in radians, convert to degrees
    local roll = math.deg(ahrs:get_roll())
    local pitch = math.deg(ahrs:get_pitch())
    local yaw = math.deg(ahrs:get_yaw())

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

    # === LOGGING ===

    "log_to_dataflash": """-- Log {sensor_name} data to dataflash

function update()
    local voltage = battery:voltage(0)
    local current = battery:current_amps(0)
    local remaining = battery:capacity_remaining_pct(0)

    if voltage and current and remaining then
        -- Log to dataflash (shows up in .bin files)
        -- Format: 'fff' = three floats
        logger:write('BATT', 'Volt,Curr,Rem', 'fff', voltage, current, remaining)
    end

    return update, 1000
end

return update()""",

    "log_to_sd_card": """-- Log battery data to CSV file on SD card

local file_name = "{log_filename}.csv"
local file

function write_to_file()
    if not file then
        gcs:send_text(3, "Could not open log file")
        return
    end

    local voltage = battery:voltage(0)
    local current = battery:current_amps(0)

    if voltage and current then
        file:write(string.format("%d,%.2f,%.2f\\n", millis(), voltage, current))
        file:flush()
    end
end

function update()
    write_to_file()
    return update, 1000
end

-- Open file for append
file = io.open(file_name, "a")
if not file then
    gcs:send_text(3, "Failed to create log file")
else
    -- Write CSV header
    file:write("Time(ms),Voltage(V),Current(A)\\n")
    file:flush()
    gcs:send_text(6, "Logging to " .. file_name)
end

return update()""",

    # === MULTI-SENSOR MONITORING ===

    "multi_sensor_status": """-- Monitor battery, GPS, and altitude - combined status report

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local voltage = battery:voltage(0)
    local num_sats = gps:num_sats(0)
    local position = ahrs:get_position()

    local status = ""

    if voltage then
        status = status .. string.format("Batt:%.1fV ", voltage)
    end

    if num_sats then
        status = status .. string.format("GPS:%dsats ", num_sats)
    end

    if position then
        local altitude = position:alt() / 100
        status = status .. string.format("Alt:%.0fm", altitude)
    end

    if string.len(status) > 0 then
        gcs:send_text(6, status)
    end

    return update, {interval}
end

return update()""",

    "dual_condition_monitor": """-- Trigger RTL if battery < {batt_threshold}% AND GPS < {gps_threshold} sats

local RTL_MODE = 6
local triggered = false

function update()
    if not arming:is_armed() then
        triggered = false
        return update, 1000
    end

    if vehicle:get_mode() == RTL_MODE or triggered then
        return update, 1000
    end

    local remaining = battery:capacity_remaining_pct(0)
    local num_sats = gps:num_sats(0)

    -- Check BOTH conditions
    if remaining and num_sats then
        if remaining < {batt_threshold} and num_sats < {gps_threshold} then
            gcs:send_text(3, string.format("RTL: Batt %.0f%% AND GPS %d sats", remaining, num_sats))
            vehicle:set_mode(RTL_MODE)
            triggered = true
        end
    end

    return update, 2000
end

return update()""",

    "multi_condition_safety": """-- Trigger RTL if ANY condition met: battery < {batt_threshold}%, GPS < {gps_threshold} sats, altitude > {alt_threshold}m

local RTL_MODE = 6
local triggered = false

function update()
    if not arming:is_armed() then
        triggered = false
        return update, 1000
    end

    if vehicle:get_mode() == RTL_MODE or triggered then
        return update, 1000
    end

    local remaining = battery:capacity_remaining_pct(0)
    local num_sats = gps:num_sats(0)
    local position = ahrs:get_position()

    -- Check battery condition
    if remaining and remaining < {batt_threshold} then
        gcs:send_text(3, string.format("RTL: Battery %.0f%%", remaining))
        vehicle:set_mode(RTL_MODE)
        triggered = true
        return update, 1000
    end

    -- Check GPS condition
    if num_sats and num_sats < {gps_threshold} then
        gcs:send_text(3, string.format("RTL: GPS %d sats", num_sats))
        vehicle:set_mode(RTL_MODE)
        triggered = true
        return update, 1000
    end

    -- Check altitude condition
    if position then
        local altitude = position:alt() / 100
        if altitude > {alt_threshold} then
            gcs:send_text(3, string.format("RTL: Altitude %.0fm", altitude))
            vehicle:set_mode(RTL_MODE)
            triggered = true
            return update, 1000
        end
    end

    return update, 2000
end

return update()""",

    # === GEOFENCE & SAFETY ===

    "geofence_monitor": """-- Monitor geofence breaches and send alerts

local breach_names = {{
    [1] = "Max altitude",
    [2] = "Circle fence",
    [4] = "Polygon fence",
    [8] = "Min altitude"
}}

function get_breach_string(breaches)
    local msg = ""
    for bitmask, name in pairs(breach_names) do
        if (breaches & bitmask) ~= 0 then
            if string.len(msg) > 0 then
                msg = msg .. " + "
            end
            msg = msg .. name
        end
    end
    return msg
end

function update()
    local breaches = fence:get_breaches()

    if breaches ~= 0 then
        local breach_time = millis() - fence:get_breach_time()
        local breach_str = get_breach_string(breaches)

        gcs:send_text(3, string.format("FENCE BREACH: %s (%.1fs)",
            breach_str, breach_time:tofloat() * 0.001))
    end

    return update, 1000
end

return update()""",

    "vibration_monitor": """-- Monitor vibration levels and warn if excessive

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local vibe = ahrs:get_vibration()

    if vibe then
        local vibe_x = vibe:x()
        local vibe_y = vibe:y()
        local vibe_z = vibe:z()

        local max_vibe = math.max(vibe_x, vibe_y, vibe_z)

        if max_vibe > {max_vibration} then
            gcs:send_text(4, string.format("High vibration: %.1f", max_vibe))
        end
    end

    return update, 5000
end

return update()""",

    "ekf_status_monitor": """-- Monitor EKF status and warn on failures

function update()
    local ekf_ok = ahrs:healthy()
    local ekf_flags = ahrs:get_ekf_status_flags()

    if not ekf_ok then
        gcs:send_text(3, "EKF NOT HEALTHY!")
    end

    -- Check critical EKF flags
    -- Bit 0: Attitude, Bit 1: Velocity Horiz, Bit 2: Velocity Vert
    -- Bit 3: Position Horiz, Bit 4: Position Vert
    if ekf_flags then
        if (ekf_flags & 1) == 0 then
            gcs:send_text(4, "EKF: Attitude estimate bad")
        end
        if (ekf_flags & 8) == 0 then
            gcs:send_text(4, "EKF: Horizontal position estimate bad")
        end
    end

    return update, 2000
end

return update()""",

    # === PARAMETER ACCESS ===

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

    "parameter_based_threshold": """-- Use {param_name} parameter as threshold for monitoring

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local threshold = param:get("{param_name}")
    local voltage = battery:voltage(0)

    if threshold and voltage then
        if voltage < threshold then
            gcs:send_text(4, string.format("Battery %.2fV below threshold %.2fV", voltage, threshold))
        end
    end

    return update, 5000
end

return update()""",

    # === STATE MACHINES ===

    "simple_state_machine": """-- Simple state machine: INIT -> WAITING -> ACTIVE -> DONE

local STATE_INIT = 0
local STATE_WAITING = 1
local STATE_ACTIVE = 2
local STATE_DONE = 3

local state = STATE_INIT

function update()
    if state == STATE_INIT then
        gcs:send_text(6, "State: INIT")
        state = STATE_WAITING

    elseif state == STATE_WAITING then
        if arming:is_armed() then
            gcs:send_text(6, "State: ACTIVE")
            state = STATE_ACTIVE
        end

    elseif state == STATE_ACTIVE then
        if not arming:is_armed() then
            gcs:send_text(6, "State: DONE")
            state = STATE_DONE
        end

    elseif state == STATE_DONE then
        -- Stay in done state
        return update, 5000
    end

    return update, 1000
end

return update()""",

    # === ADVANCED MONITORING ===

    "wind_speed_monitor": """-- Monitor wind speed and warn if exceeds {max_speed} m/s

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local wind = ahrs:wind_estimate()

    if wind then
        local wind_speed = wind:length()
        if wind_speed > {max_speed} then
            gcs:send_text(4, string.format("High wind: %.1f m/s", wind_speed))
        end
    end

    return update, 5000
end

return update()""",

    "motor_status_monitor": """-- Monitor motor armed status and send notifications

local last_motor_state = false

function update()
    local motors_armed = motors:get_interlock()

    if motors_armed ~= last_motor_state then
        if motors_armed then
            gcs:send_text(6, "Motors ARMED")
        else
            gcs:send_text(6, "Motors DISARMED")
        end
        last_motor_state = motors_armed
    end

    return update, 100
end

return update()""",

    "current_measurement": """-- Display battery current draw

function update()
    local current = battery:current_amps(0)

    if current then
        gcs:send_text(6, string.format("Battery current: %.2f A", current))
    else
        gcs:send_text(4, "Could not read current")
    end

    return update, {interval}
end

return update()""",

    "battery_capacity_monitor": """-- Monitor battery remaining capacity and warn if below {min_capacity} mAh

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local capacity = battery:capacity_remaining(0)

    if capacity and capacity < {min_capacity} then
        gcs:send_text(4, string.format("Low capacity: %d mAh", capacity))
    end

    return update, 5000
end

return update()""",

    "barometer_health_check": """-- Check barometer health and send status

function update()
    local healthy = baro:healthy(0)
    local pressure = baro:get_pressure(0)
    local temperature = baro:get_temperature(0)

    if not healthy then
        gcs:send_text(3, "Barometer NOT healthy!")
    else
        if pressure and temperature then
            gcs:send_text(6, string.format("Baro: %.1f Pa, %.1f C", pressure, temperature))
        end
    end

    return update, {interval}
end

return update()""",

    "home_distance_monitor": """-- Calculate and display distance from home position

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local home = ahrs:get_home()
    local current = ahrs:get_position()

    if home and current then
        local distance = home:get_distance(current)
        gcs:send_text(6, string.format("Distance from home: %.1f m", distance))
    end

    return update, {interval}
end

return update()""",

    "servo_control": """-- Set servo channel {channel} to {pwm} PWM when armed

function update()
    if arming:is_armed() then
        SRV_Channels:set_output_pwm({channel}, {pwm})
    end

    return update, 1000
end

return update()""",

    "led_blink_pattern": """-- LED blink pattern: {blink_count} times when disarmed

local last_armed = true
local blink_stage = 0
local max_blinks = {blink_count}

function update()
    local armed = arming:is_armed()

    -- Detect disarm event
    if last_armed and not armed then
        blink_stage = 1
    end

    -- Blink sequence
    if blink_stage > 0 and blink_stage <= max_blinks * 2 then
        if blink_stage % 2 == 1 then
            notify:play_tune("MFT200L4>C")  -- Short beep
        end
        blink_stage = blink_stage + 1
    elseif blink_stage > max_blinks * 2 then
        blink_stage = 0
    end

    last_armed = armed
    return update, 200
end

return update()""",

    "gps_hdop_monitor": """-- Monitor GPS HDOP and warn if exceeds {max_hdop}

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    local hdop = gps:get_hdop(0)

    if hdop then
        local hdop_value = hdop / 100  -- Convert to float
        if hdop_value > {max_hdop} then
            gcs:send_text(4, string.format("High HDOP: %.1f", hdop_value))
        end
    end

    return update, 5000
end

return update()""",

    "mission_status_monitor": """-- Monitor mission progress and send status updates

local last_mission_num = -1

function update()
    if not arming:is_armed() then
        return update, 1000
    end

    if vehicle:get_mode() == 3 then  -- AUTO mode
        local mission_num = mission:get_current_nav_index()
        local mission_total = mission:num_commands()

        if mission_num ~= last_mission_num then
            gcs:send_text(6, string.format("Mission: %d/%d", mission_num, mission_total))
            last_mission_num = mission_num
        end
    end

    return update, 1000
end

return update()""",
}


# ========== INTENT DETECTION ==========

INTENT_PATTERNS = {
    # Basic monitoring
    "battery_voltage_monitor": [
        r'battery.*voltage.*monitor',
        r'monitor.*battery.*voltage',
        r'battery.*warn.*\d+\.?\d*v',
        r'warn.*battery.*below',
        r'check.*battery.*voltage',
    ],
    "gps_satellite_monitor": [
        r'gps.*satellite',
        r'monitor.*gps',
        r'satellite.*count',
        r'gps.*warn.*\d+',
        r'check.*gps.*sat',
    ],
    "altitude_monitor": [
        r'altitude.*exceed',
        r'altitude.*warning',
        r'altitude.*above.*\d+',
        r'warn.*altitude',
        r'monitor.*altitude',
    ],
    "rangefinder_monitor": [
        r'rangefinder.*below',
        r'rangefinder.*warning',
        r'rangefinder.*distance',
        r'warn.*rangefinder',
        r'monitor.*rangefinder',
    ],

    # Autonomous actions
    "auto_rtl_battery": [
        r'auto.*rtl.*battery',
        r'rtl.*battery.*\d+',
        r'trigger.*rtl.*battery',
        r'battery.*rtl',
        r'rtl.*when.*battery',
    ],
    "auto_land_altitude": [
        r'auto.*land.*altitude',
        r'land.*altitude.*\d+',
        r'trigger.*land.*altitude',
        r'altitude.*land',
    ],

    # Arming checks
    "battery_temp_arming_check": [
        r'arming.*check.*battery.*temp',
        r'prevent.*arming.*temp',
        r'battery.*temp.*arming',
        r'arming.*battery.*temperature',
    ],
    "battery_resistance_check": [
        r'arming.*check.*resistance',
        r'resistance.*arming',
        r'internal.*resistance',
        r'battery.*resistance.*arming',
    ],
    "gps_arming_check": [
        r'arming.*check.*gps',
        r'gps.*arming',
        r'prevent.*arming.*gps',
        r'arming.*satellite',
    ],

    # Attitude
    "attitude_monitor": [
        r'attitude.*roll.*pitch.*yaw',
        r'monitor.*attitude.*rotation',
        r'roll.*pitch.*yaw.*rate',
        r'attitude.*rate',
    ],

    # Logging
    "log_to_dataflash": [
        r'log.*dataflash',
        r'dataflash.*log',
        r'log.*\.bin',
        r'write.*dataflash',
    ],
    "log_to_sd_card": [
        r'log.*sd.*card',
        r'log.*csv',
        r'csv.*log',
        r'write.*sd.*card',
        r'save.*sd.*card',
    ],

    # Multi-sensor (check these BEFORE basic monitoring)
    "multi_sensor_status": [
        r'battery.*gps.*altitude',
        r'combined.*status.*message',
        r'multi.*sensor.*status',
        r'status.*report.*every',
        r'monitor.*battery.*gps.*altitude',
    ],
    "dual_condition_monitor": [
        r'both.*battery.*and.*gps',
        r'both.*gps.*and.*battery',
        r'battery.*and.*gps',
        r'rtl.*both',
        r'and.*gps.*sat',
    ],
    "multi_condition_safety": [
        r'any\s+of',
        r'either.*or',
        r'battery.*gps.*altitude.*rtl',
        r'multiple.*condition.*rtl',
        r'if.*<.*<.*>',  # Detects multiple conditions with comparison operators
    ],

    # Safety
    "geofence_monitor": [
        r'geofence.*breach',
        r'fence.*breach',
        r'monitor.*fence',
        r'geofence.*monitor',
    ],
    "vibration_monitor": [
        r'vibration.*monitor',
        r'monitor.*vibration',
        r'vibration.*level',
        r'check.*vibration',
    ],
    "ekf_status_monitor": [
        r'ekf.*status',
        r'monitor.*ekf',
        r'ekf.*health',
        r'check.*ekf',
    ],

    # Parameters
    "parameter_reader": [
        r'read.*parameter',
        r'parameter.*display',
        r'show.*parameter',
        r'get.*parameter',
    ],
    "parameter_based_threshold": [
        r'parameter.*threshold',
        r'use.*parameter.*as',
        r'threshold.*parameter',
        r'param.*based',
    ],

    # State machines
    "simple_state_machine": [
        r'state.*machine',
        r'init.*waiting.*active',
        r'three.*state',
        r'state.*transition',
    ],

    # Advanced monitoring
    "wind_speed_monitor": [
        r'wind.*speed',
        r'monitor.*wind',
        r'wind.*warn',
        r'wind.*exceed',
    ],
    "motor_status_monitor": [
        r'motor.*status',
        r'motor.*armed',
        r'motors.*state',
        r'check.*motor',
    ],
    "current_measurement": [
        r'current.*draw',
        r'battery.*current',
        r'display.*current',
        r'show.*current',
        r'measure.*current',
    ],
    "battery_capacity_monitor": [
        r'capacity.*mah',
        r'remaining.*mah',
        r'battery.*capacity.*warn',
        r'monitor.*capacity.*mah',
    ],
    "barometer_health_check": [
        r'barometer.*health',
        r'baro.*health',
        r'barometer.*status',
        r'check.*barometer',
    ],
    "home_distance_monitor": [
        r'distance.*from.*home',
        r'home.*distance',
        r'distance.*home.*position',
        r'calculate.*distance.*home',
    ],
    "servo_control": [
        r'servo.*channel.*\d+',
        r'set.*servo.*pwm',
        r'servo.*\d+.*pwm',
        r'control.*servo',
    ],
    "led_blink_pattern": [
        r'led.*blink.*\d+',
        r'blink.*\d+.*times',
        r'led.*pattern',
        r'flash.*led.*\d+',
    ],
    "gps_hdop_monitor": [
        r'gps.*hdop',
        r'hdop.*monitor',
        r'hdop.*exceed',
        r'hdop.*warn',
    ],
    "mission_status_monitor": [
        r'mission.*status',
        r'mission.*progress',
        r'monitor.*mission',
        r'mission.*waypoint',
    ],
}


def detect_intent(user_request: str) -> str:
    """Detect which template best matches user's request"""

    user_lower = user_request.lower()

    # Priority order: Check complex patterns first, then basic ones
    priority_order = [
        # Multi-condition patterns (check first!)
        "multi_condition_safety",
        "dual_condition_monitor",
        "multi_sensor_status",

        # Logging patterns
        "log_to_sd_card",
        "log_to_dataflash",

        # Safety monitoring
        "geofence_monitor",
        "vibration_monitor",
        "ekf_status_monitor",

        # Arming checks
        "battery_temp_arming_check",
        "battery_resistance_check",
        "gps_arming_check",

        # Autonomous actions
        "auto_land_altitude",
        "auto_rtl_battery",

        # Advanced monitoring
        "mission_status_monitor",
        "home_distance_monitor",
        "servo_control",
        "led_blink_pattern",
        "gps_hdop_monitor",
        "battery_capacity_monitor",
        "barometer_health_check",
        "wind_speed_monitor",
        "motor_status_monitor",
        "current_measurement",

        # Parameter access
        "parameter_based_threshold",
        "parameter_reader",

        # State machines
        "simple_state_machine",

        # Basic monitoring (check last!)
        "rangefinder_monitor",
        "altitude_monitor",
        "gps_satellite_monitor",
        "battery_voltage_monitor",
        "attitude_monitor",
    ]

    # Score each template
    scores = {}
    for template_name, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, user_lower):
                score += 1
        if score > 0:
            scores[template_name] = score

    if not scores:
        return None

    # If we have scores, apply priority weighting
    # Templates earlier in priority_order get bonus points
    weighted_scores = {}
    for template_name, score in scores.items():
        if template_name in priority_order:
            priority_bonus = (len(priority_order) - priority_order.index(template_name)) * 0.1
            weighted_scores[template_name] = score + priority_bonus
        else:
            weighted_scores[template_name] = score

    # Return best match
    return max(weighted_scores.items(), key=lambda x: x[1])[0]


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
        if template_name == "gps_arming_check":
            params["min_sats"] = match.group(1) if match else "6"
        else:
            params["min_sats"] = match.group(1) if match else "6"

    # Altitude
    if "altitude" in template_name:
        match = re.search(r'(\d+)\s*m', user_request, re.IGNORECASE)
        if "auto_land" in template_name:
            params["min_altitude"] = match.group(1) if match else "5"
        else:
            params["max_alt"] = match.group(1) if match else "100"

    # Rangefinder
    if "rangefinder" in template_name:
        match = re.search(r'(\d+\.?\d*)\s*m', user_request, re.IGNORECASE)
        params["min_distance"] = match.group(1) if match else "2.0"

    # Battery percentage for RTL
    if "rtl" in template_name and "battery" in template_name:
        match = re.search(r'(\d+)%', user_request)
        if "dual_condition" in template_name:
            params["batt_threshold"] = match.group(1) if match else "25"
        else:
            params["threshold"] = match.group(1) if match else "20"

    # Temperature
    if "temp" in template_name:
        match = re.search(r'(\d+)\s*[°c]', user_request, re.IGNORECASE)
        params["max_temp"] = match.group(1) if match else "45"

    # Resistance
    if "resistance" in template_name:
        match = re.search(r'(\d+\.?\d*)\s*ohm', user_request, re.IGNORECASE)
        params["max_resistance"] = match.group(1) if match else "0.03"

    # Vibration
    if "vibration" in template_name:
        match = re.search(r'(\d+\.?\d*)', user_request)
        params["max_vibration"] = match.group(1) if match else "30.0"

    # Multi-sensor interval
    if "multi_sensor" in template_name:
        match = re.search(r'every\s+(\d+)\s+second', user_request, re.IGNORECASE)
        params["interval"] = str(int(match.group(1)) * 1000) if match else "10000"

    # Dual condition (battery AND gps)
    if "dual_condition" in template_name:
        batt_match = re.search(r'battery.*?(\d+)%', user_request, re.IGNORECASE)
        gps_match = re.search(r'gps.*?(\d+)\s*sat', user_request, re.IGNORECASE)
        params["batt_threshold"] = batt_match.group(1) if batt_match else "25"
        params["gps_threshold"] = gps_match.group(1) if gps_match else "5"

    # Multi-condition safety (battery OR gps OR altitude)
    if "multi_condition" in template_name:
        batt_match = re.search(r'battery.*?(\d+)%', user_request, re.IGNORECASE)
        gps_match = re.search(r'gps.*?(\d+)\s*sat', user_request, re.IGNORECASE)
        alt_match = re.search(r'altitude.*?(\d+)\s*m', user_request, re.IGNORECASE)
        params["batt_threshold"] = batt_match.group(1) if batt_match else "15"
        params["gps_threshold"] = gps_match.group(1) if gps_match else "4"
        params["alt_threshold"] = alt_match.group(1) if alt_match else "150"

    # Logging filename
    if "log_to_sd_card" in template_name:
        params["log_filename"] = "battery_log"

    # Logging sensor name
    if "log_to_dataflash" in template_name:
        params["sensor_name"] = "battery"

    # Parameter name
    if "parameter" in template_name:
        match = re.search(r'([A-Z_]+)', user_request)
        params["param_name"] = match.group(1) if match else "WPNAV_SPEED"

    # Wind speed
    if "wind_speed" in template_name:
        match = re.search(r'(\d+\.?\d*)\s*m/s', user_request, re.IGNORECASE)
        params["max_speed"] = match.group(1) if match else "15.0"

    # Battery capacity (mAh)
    if "battery_capacity" in template_name:
        match = re.search(r'(\d+)\s*mah', user_request, re.IGNORECASE)
        params["min_capacity"] = match.group(1) if match else "1000"

    # Barometer / home distance / current interval
    if template_name in ["barometer_health_check", "home_distance_monitor", "current_measurement"]:
        match = re.search(r'every\s+(\d+)\s+second', user_request, re.IGNORECASE)
        params["interval"] = str(int(match.group(1)) * 1000) if match else "30000"

    # Servo control
    if "servo" in template_name:
        channel_match = re.search(r'channel\s+(\d+)', user_request, re.IGNORECASE)
        pwm_match = re.search(r'(\d+)\s*pwm', user_request, re.IGNORECASE)
        params["channel"] = channel_match.group(1) if channel_match else "9"
        params["pwm"] = pwm_match.group(1) if pwm_match else "1500"

    # LED blink pattern
    if "led_blink" in template_name:
        match = re.search(r'(\d+)\s*time', user_request, re.IGNORECASE)
        params["blink_count"] = match.group(1) if match else "3"

    # GPS HDOP
    if "hdop" in template_name:
        match = re.search(r'(\d+\.?\d*)', user_request)
        params["max_hdop"] = match.group(1) if match else "2.0"

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


# ========== TESTING ==========

if __name__ == "__main__":
    test_requests = [
        # Basic monitoring
        "Monitor battery voltage and warn if below 11.5V",
        "Create script to monitor GPS satellites and warn if below 6",
        "Send warning if altitude exceeds 100 meters",
        "Warn if rangefinder distance is below 2 meters",

        # Autonomous actions
        "Automatically trigger RTL when battery drops below 20%",
        "Auto land when altitude is below 5 meters",

        # Arming checks
        "Create an arming check that prevents arming if battery temperature exceeds 45°C",
        "Create pre-arm check for battery internal resistance above 0.03 Ohms",
        "Prevent arming if GPS has less than 8 satellites",

        # Multi-sensor
        "Monitor battery voltage, GPS satellites, and altitude. Send a combined status message every 10 seconds",
        "Trigger RTL if BOTH battery is below 25% AND GPS satellites drop below 5",
        "Trigger RTL if ANY of: battery < 15%, GPS < 4 sats, altitude > 150m",

        # Logging
        "Create a script that logs battery voltage to SD card in CSV format",
        "Log battery data to dataflash",

        # Safety
        "Monitor geofence breaches and send alerts",
        "Monitor vibration levels and warn if excessive",
        "Monitor EKF status and warn on failures",

        # Advanced monitoring (NEW!)
        "Warn if wind speed exceeds 15 m/s",
        "Monitor motor armed status and send notifications",
        "Display battery current draw every 10 seconds",
        "Monitor battery remaining capacity and warn if below 1000 mAh",
        "Check barometer health and send status every 30 seconds",
        "Calculate and display distance from home position every 5 seconds",
        "Set servo channel 9 to 1500 PWM when armed",
        "LED blink pattern that flashes 3 times when disarmed",
        "Monitor GPS HDOP and warn if exceeds 2.0",
        "Monitor mission progress and send status updates",
    ]

    print("=" * 80)
    print("TEMPLATE INJECTION SYSTEM V2 - TEST")
    print("=" * 80)
    print(f"\nTotal templates: {len(TEMPLATES)}")
    print(f"Total intent patterns: {len(INTENT_PATTERNS)}")
    print()

    matched = 0
    for i, request in enumerate(test_requests, 1):
        print(f"\n[{i}] Request: {request}")
        code, template = generate_from_template(request)

        if code:
            matched += 1
            print(f"    [OK] Template: {template}")
            print(f"    [OK] Code length: {len(code)} chars")
        else:
            print("    [MISS] No template match - will use LLM")

    print()
    print("=" * 80)
    print(f"Results: {matched}/{len(test_requests)} matched ({matched * 100 // len(test_requests)}%)")
    print("=" * 80)
