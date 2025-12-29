# Testing Guide for New Functions

## Quick Test Commands

### Test Composite Functions

**1. Arm and Takeoff**
```
User: "arm and takeoff to 10 meters"
Expected: arm_and_takeoff(altitude=10)
Result: Drone arms and takes off to 10m in one command
```

**2. Hover**
```
User: "hold position for 5 seconds"
Expected: hover(duration=5)
Result: Drone holds current position for 5 seconds
```

**3. Land and Disarm**
```
User: "land and disarm"
Expected: land_and_disarm()
Result: Drone lands and automatically disarms
```

### Test Parameter Control

**4. Set Parameter**
```
User: "set waypoint speed to 500"
Expected: set_parameter(param_name="WPNAV_SPEED", value=500)
Result: WPNAV_SPEED parameter set to 500 cm/s
```

**5. Get Parameter**
```
User: "get RTL altitude"
Expected: get_parameter(param_name="RTL_ALT")
Result: Returns current RTL_ALT value
```

### Test Advanced Control

**6. Set Yaw**
```
User: "set heading to 90 degrees"
Expected: set_yaw(angle=90, relative=False)
Result: Drone points east (90°)
```

**7. Emergency Stop**
```
User: "emergency stop"
Expected: emergency_stop()
Result: Motors stop immediately (USE WITH CAUTION!)
```

## Multi-Step Command Examples

**Example 1: Full Flight Sequence**
```
1. "arm and takeoff to 15 meters"
2. "hold position for 3 seconds"
3. "increase altitude by 5 meters"
4. "hold for 2 seconds"
5. "land and disarm"
```

**Example 2: Parameter Configuration**
```
1. "set waypoint speed to 300"
2. "get waypoint speed parameter"
3. "arm and takeoff to 10 meters"
4. "go to guided mode"
```

**Example 3: Navigation Pattern**
```
1. "arm and takeoff to 20 meters"
2. "set heading to 0 degrees"
3. "move north 10 meters"
4. "set heading to 90 degrees"
5. "move east 10 meters"
6. "land and disarm"
```

## SITL Testing Steps

### 1. Start SITL
```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -w --console --map
```

### 2. Start AI Assistant
```bash
cd ~/Documents/Projects/AP_Offline_chat_tools
python main.py
```

### 3. Test Basic Composite
```
arm and takeoff to 10 meters
```

### 4. Test Hover
```
hold position for 5 seconds
```

### 5. Test Parameters
```
set WPNAV_SPEED to 500
get WPNAV_SPEED
```

### 6. Test Full Sequence
```
arm and takeoff to 15 meters
[wait for completion]
hold for 3 seconds
[wait]
land and disarm
```

## Expected Results

### arm_and_takeoff
- ✅ Drone arms (motors spin)
- ✅ Switches to GUIDED mode
- ✅ Takes off to specified altitude
- ✅ Single command instead of two

### hover
- ✅ Switches to LOITER mode
- ✅ Holds position for duration
- ✅ Returns success after duration

### land_and_disarm
- ✅ Switches to LAND mode
- ✅ Descends to ground
- ✅ Automatically disarms motors

### set_parameter
- ✅ Parameter value updated
- ✅ Confirmation message
- ✅ Value persists

### get_parameter
- ✅ Returns current parameter value
- ✅ Shows parameter name and value

## Common Issues & Solutions

### Issue: "arm_and_takeoff not found"
**Solution**: Restart main.py to reload functions

### Issue: "hover doesn't work"
**Solution**: Ensure drone is armed and airborne first

### Issue: "parameter not found"
**Solution**: Check parameter name spelling (case-sensitive)

### Issue: "emergency_stop too dangerous"
**Solution**: Only use in actual emergencies, drone will fall!

## Function Count Summary

**Total Functions**: 38

- Basic Control: 8
- Composite: 3 (NEW!)
- Navigation: 8
- Status: 3
- Parameters: 2 (NEW!)
- Emergency: 1 (NEW!)
- Mission: 10
- Speed: 1
- Advanced: 2 (NEW!)

## Next Steps

1. ✅ Test all 7 new functions
2. ✅ Verify parameter control works
3. ✅ Test multi-step sequences
4. 🔄 Implement pipeline executor (future)
5. 🔄 Add conditional logic (future)
