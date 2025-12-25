# Quick Reference Card

## 🚁 ArduPilot AI Assistant - Command Cheat Sheet

### ✈️ Basic Flight Commands

```bash
# Arm & Takeoff
arm the drone
takeoff to 15 meters          # ✅ Use "to" not "at"
takeoff to 20m
take off to 10 meters

# Land & Return
land the drone
land
return to launch
return home
RTL
```

### 📊 Status Commands

```bash
# Battery
check battery                 # → 🔋 Battery: 12.60V, 8.50A, 87% remaining
battery status
battery health

# Position
where am I?                   # → 📍 Position: Lat X°, Lon Y°, Alt Zm, Heading H°
get position
current position
```

### 🎮 Mode Changes

```bash
change mode to GUIDED
change mode to LOITER
change mode to RTL
change mode to LAND
switch to LOITER
```

### 🛑 Safety

```bash
disarm the drone
disarm
```

---

## ⚠️ Common Mistakes

| ❌ Don't Say | ✅ Say Instead |
|-------------|---------------|
| `takeoff drone at 29` | `takeoff to 29 meters` |
| `arm drone` | `arm the drone` |
| `fly up to 15` | `takeoff to 15 meters` |
| `change to GUIDED` | `change mode to GUIDED` |
| `how much battery` | `check battery` |

---

## 💡 Pro Tips

1. **Use "to" for takeoff**: `takeoff to 15 meters` ✅
2. **Include "the"**: `arm the drone` ✅
3. **Say "mode"**: `change mode to GUIDED` ✅
4. **Be specific**: Use exact numbers and mode names

---

## 🔧 Special Commands

```bash
/help or /h      # Show available functions
/status or /s    # Get drone status (battery + position)
/reset or /r     # Clear conversation history
/quit or /q      # Exit application
```

---

## 📖 Full Documentation

- **Command Reference**: `docs/COMMAND_REFERENCE.md`
- **README**: `README.md`
- **Contributing**: `CONTRIBUTING.md`

---

**Model:** ardupilot-stage1 | **Accuracy:** 85% | **Functions:** 8/29
