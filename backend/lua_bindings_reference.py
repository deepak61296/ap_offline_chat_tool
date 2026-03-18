"""ArduPilot Lua scripting bindings reference for script generation."""

LUA_BINDINGS_REFERENCE = """
# ArduPilot Lua 5.3 Scripting Reference

## Common Bindings

### GCS (Ground Control Station) - gcs:
- `gcs:send_text(severity, text)` - Send text message to GCS
  - severity: 0=EMERGENCY, 1=ALERT, 2=CRITICAL, 3=ERROR, 4=WARNING, 5=NOTICE, 6=INFO, 7=DEBUG
  - Example: `gcs:send_text(6, "Script started")`

### AHRS (Attitude and Heading Reference System) - ahrs:
- `ahrs:get_home()` - Get home location (Location object)
- `ahrs:get_position()` - Get current position (Location object)
- `ahrs:get_gyro()` - Get gyro data (Vector3f)
- `ahrs:get_hagl()` - Get height above ground level (meters)

### Arming - arming:
- `arming:is_armed()` - Check if vehicle is armed (boolean)
- `arming:arm()` - Arm the vehicle (boolean, requires safety checks)
- `arming:disarm()` - Disarm the vehicle (boolean)

### Battery - battery:
- `battery:num_instances()` - Number of battery instances
- `battery:healthy(instance)` - Check if battery healthy (boolean)
- `battery:voltage(instance)` - Battery voltage in Volts
- `battery:current_amps(instance)` - Current in Amperes
- `battery:consumed_mah(instance)` - Consumed capacity in mAh
- `battery:capacity_remaining_pct(instance)` - Remaining percentage (0-100)
- `battery:get_temperature(instance)` - Battery temperature in Celsius

### GPS - gps:
- `gps:num_sensors()` - Number of GPS sensors
- `gps:status(instance)` - GPS status (0=NO_GPS, 3=GPS_OK_FIX_3D)
- `gps:num_sats(instance)` - Number of satellites
- `gps:location(instance)` - Get GPS location (Location object)
- `gps:speed_accuracy(instance)` - Speed accuracy estimate
- `gps:horizontal_accuracy(instance)` - Horizontal position accuracy

### Vehicle - vehicle:
- `vehicle:set_mode(mode_number)` - Change flight mode
  - Copter: 0=STABILIZE, 1=ACRO, 2=ALT_HOLD, 3=AUTO, 4=GUIDED, 5=LOITER, 6=RTL, 9=LAND
- `vehicle:get_mode()` - Get current mode number
- `vehicle:set_target_location(location)` - Set target in GUIDED mode
- `vehicle:set_target_velocity_NED(velocity_vector)` - Set velocity in North-East-Down
- `vehicle:set_circle_mode(center, radius, altitude)` - Circle around point

### Location Object:
- `Location()` - Create new location
- Methods: `lat()`, `lng()`, `alt()`, `get_distance(other_location)`, `offset(north_m, east_m)`

### Vector3f Object:
- `Vector3f()` - Create 3D vector
- Methods: `x()`, `y()`, `z()`, `length()`

### Mission - mission:
- `mission:num_commands()` - Total waypoints
- `mission:get_current_nav_index()` - Current waypoint index
- `mission:set_current_index(index)` - Jump to waypoint

### Servo/Motor - SRV_Channels:
- `SRV_Channels:set_output_pwm(channel, pwm)` - Set servo PWM (typical: 1000-2000)

### Parameters - param:
- `param:get(name)` - Get parameter value
- `param:set(name, value)` - Set parameter value
- `param:set_and_save(name, value)` - Set and save to EEPROM

## Script Structure

Every Lua script must:
1. Define an update function that returns itself and delay in milliseconds
2. Return the update function to start execution

Example:
```lua
function update()
    -- Your code here
    return update, 1000  -- Run every 1000ms (1 second)
end

return update()
```

## Safety Best Practices

1. Always check arming status before movement commands
2. Verify GPS lock before navigation
3. Monitor battery levels
4. Include timeout conditions
5. Add GCS notifications for important events
6. Handle errors gracefully

## Example Patterns

### Pattern 1: State Machine
```lua
local STATE_INIT = 0
local STATE_RUNNING = 1
local current_state = STATE_INIT

function update()
    if current_state == STATE_INIT then
        -- Initialization
        current_state = STATE_RUNNING
    elseif current_state == STATE_RUNNING then
        -- Main logic
    end
    return update, 1000
end
return update()
```

### Pattern 2: Conditional Safety Check
```lua
function update()
    if not arming:is_armed() then
        gcs:send_text(6, "Waiting for arm")
        return update, 1000
    end
    
    local battery_remaining = battery:capacity_remaining_pct(0)
    if battery_remaining < 20 then
        gcs:send_text(3, "Low battery! RTL")
        vehicle:set_mode(6)  -- RTL
    end
    
    return update, 5000
end
return update()
```

### Pattern 3: Mission Monitoring
```lua
function update()
    local current_wp = mission:get_current_nav_index()
    local total_wp = mission:num_commands()
    
    gcs:send_text(6, string.format("WP %d/%d", current_wp, total_wp))
    
    return update, 2000
end
return update()
```
"""

# Common use case templates
LUA_TEMPLATES = {
    "circle": """
-- Circle around home location
local home = ahrs:get_home()
local radius = {radius}
local altitude = {altitude}

function update()
    if not arming:is_armed() then
        gcs:send_text(6, "Waiting for arm")
        return update, 1000
    end
    
    vehicle:set_circle_mode(home, radius, altitude)
    gcs:send_text(6, string.format("Circling at %.0fm altitude", altitude))
    
    return update, 1000
end

return update()
""",
    
    "battery_monitor": """
-- Monitor battery and RTL when low
local RTL_BATTERY_PERCENT = {threshold}

function update()
    local remaining = battery:capacity_remaining_pct(0)
    local voltage = battery:voltage(0)
    
    if remaining < RTL_BATTERY_PERCENT and arming:is_armed() then
        gcs:send_text(3, string.format("Low battery! %.1f%% remaining - RTL", remaining))
        vehicle:set_mode(6)  -- RTL mode
    end
    
    return update, 5000  -- Check every 5 seconds
end

return update()
""",
    
    "altitude_monitor": """
-- Monitor altitude and notify on changes
local last_altitude = 0
local ALERT_THRESHOLD = {threshold}

function update()
    local current_alt = ahrs:get_hagl()
    local change = math.abs(current_alt - last_altitude)
    
    if change > ALERT_THRESHOLD then
        gcs:send_text(6, string.format("Altitude: %.1fm (change: %.1fm)", current_alt, change))
        last_altitude = current_alt
    end
    
    return update, 1000
end

return update()
"""
}
