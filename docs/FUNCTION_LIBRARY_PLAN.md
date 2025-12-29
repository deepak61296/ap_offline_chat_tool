# Function Library Expansion Plan

## Current Function Analysis

### ✅ Currently Implemented (31 functions)

#### Basic Control (8 functions)
1. **arm()** - Arm motors ✅
2. **disarm()** - Disarm motors ✅
3. **takeoff(altitude)** - Takeoff to altitude ✅
4. **land()** - Land at current location ✅
5. **rtl()** - Return to launch ✅
6. **change_mode(mode)** - Change flight mode ✅
7. **get_mode()** - Get current mode ✅
8. **is_armable()** - Check if ready to arm ✅

#### Navigation (7 functions)
9. **goto_location(lat, lon, alt)** - Go to GPS coordinates ✅
10. **increase_altitude(meters)** - Climb by X meters ✅
11. **decrease_altitude(meters)** - Descend by X meters ✅
12. **move_north(meters)** - Move north ✅
13. **move_south(meters)** - Move south ✅
14. **move_east(meters)** - Move east ✅
15. **move_west(meters)** - Move west ✅
16. **move_relative(north, east, down)** - NED movement ✅

#### Status/Info (3 functions)
17. **get_position()** - Get GPS position ✅
18. **get_battery()** - Get battery status ✅
19. **get_current_altitude()** - Get altitude ✅

#### Speed Control (1 function)
20. **set_speed(speed, type)** - Set ground/air speed ✅

#### Mission Planning (10 functions)
21. **create_mission()** - Start new mission ✅
22. **add_takeoff_waypoint(alt)** - Add takeoff to mission ✅
23. **add_waypoint(lat, lon, alt)** - Add GPS waypoint ✅
24. **add_relative_waypoint(n, e, alt)** - Add relative waypoint ✅
25. **add_land_waypoint()** - Add land to mission ✅
26. **get_mission_summary()** - Get mission info ✅
27. **upload_mission()** - Upload mission to drone ✅
28. **start_mission()** - Start mission execution ✅
29. **clear_mission()** - Clear mission ✅
30. **set_speed(speed)** - Set vehicle speed ✅

## ❌ Missing Critical Functions

### Composite Functions (High Priority)
- **arm_and_takeoff(altitude)** - Arm + takeoff in one command
- **land_and_disarm()** - Land + disarm automatically
- **hover(duration)** - Hold position for X seconds
- **circle(radius, duration)** - Circle at current location

### Parameter Configuration (High Priority)
- **set_parameter(name, value)** - Set any ArduPilot parameter
- **get_parameter(name)** - Get parameter value
- **set_failsafe(type, action)** - Configure failsafes
- **set_geofence(radius, max_alt)** - Set geofence limits

### Advanced Navigation
- **orbit_location(lat, lon, radius)** - Orbit a point
- **follow_path(waypoints)** - Follow multiple waypoints
- **set_yaw(angle)** - Set heading
- **set_roi(lat, lon, alt)** - Point camera at location

### Safety & Monitoring
- **emergency_stop()** - Emergency motor stop
- **get_system_status()** - Full system health
- **get_gps_status()** - GPS fix quality
- **get_vibration()** - Vibration levels

### Multi-Step Command Support
- **execute_sequence(commands)** - Run multiple commands
- **conditional_command(condition, then, else)** - If-then logic

## 🎯 Implementation Priority

### Phase 1: Composite Functions (IMMEDIATE)
These are most requested and easy to implement:

```python
def arm_and_takeoff(altitude: float) -> Dict[str, Any]:
    """Arm motors and takeoff to altitude in one command"""
    
def hover(duration: float) -> Dict[str, Any]:
    """Hold current position for duration seconds"""
    
def land_and_disarm() -> Dict[str, Any]:
    """Land and automatically disarm"""
```

### Phase 2: Parameter Configuration (HIGH)
Essential for full drone control:

```python
def set_parameter(param_name: str, value: float) -> Dict[str, Any]:
    """Set ArduPilot parameter (e.g., 'WPNAV_SPEED', 500)"""
    
def get_parameter(param_name: str) -> Dict[str, Any]:
    """Get parameter value"""
```

### Phase 3: Multi-Step Execution (CRITICAL)
Enable complex commands like "arm, takeoff to 10m, hold 5 sec, then RTL":

```python
def execute_pipeline(steps: List[Dict]) -> Dict[str, Any]:
    """Execute multiple commands in sequence with delays"""
```

### Phase 4: Advanced Features
- Orbit/circle patterns
- ROI (Region of Interest)
- Geofencing
- Advanced failsafes

## 🤖 AI Model Updates Needed

### Current Qwen 2.5 Prompt Needs:
1. **Add new functions** to system prompt
2. **Enable multi-step reasoning** for pipeline commands
3. **Add delay/wait capability** between commands

### Example Multi-Step Command:
```
User: "arm drone, takeoff to 10m, hold for 5 seconds, then RTL"

AI Should Parse To:
[
  {"function": "arm_and_takeoff", "parameters": {"altitude": 10}},
  {"function": "hover", "parameters": {"duration": 5}},
  {"function": "rtl", "parameters": {}}
]
```

## 📋 Function Summary Document

### What We Can Do Now:
✅ Basic flight (arm, takeoff, land, RTL)
✅ Altitude control (increase/decrease)
✅ Directional movement (N/S/E/W)
✅ Mode changes (GUIDED, LOITER, etc.)
✅ Status queries (battery, position, mode)
✅ Mission planning (create, upload, execute)
✅ Speed control

### What We CANNOT Do Yet:
❌ Arm and takeoff in one command
❌ Hold/hover for duration
❌ Set ArduPilot parameters
❌ Multi-step command sequences
❌ Conditional logic
❌ Emergency procedures
❌ Advanced patterns (circle, orbit)
❌ Camera control (ROI)

## 🚀 Recommended Next Steps

1. **Implement arm_and_takeoff()** - Most requested
2. **Implement hover(duration)** - Essential for sequences
3. **Implement set_parameter()** - Full configurability
4. **Update Qwen prompt** - Add new functions
5. **Add pipeline executor** - Multi-step commands
6. **Test with SITL** - Verify all functions work

## 📊 Impact Analysis

### Current Limitations:
- User must give separate "arm" then "takeoff" commands
- Cannot execute "do X, wait Y seconds, then do Z"
- Cannot configure drone parameters via AI
- No emergency procedures
- Limited to simple single-step commands

### After Implementation:
- ✅ Natural multi-step commands
- ✅ Full parameter control
- ✅ Complex flight patterns
- ✅ Emergency handling
- ✅ Production-ready system

---

**Ready to implement Phase 1 composite functions?**
