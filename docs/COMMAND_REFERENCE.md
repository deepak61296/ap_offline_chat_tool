# Command Reference Guide

## 🎯 Natural Language Commands for Stage 1 Functions

This guide shows **tested phrasings** that work with the Stage 1 model. The model was trained on specific phrasings, so using these exact patterns will give the best results.

---

## ✅ Working Commands by Function

### 1. arm()

**Tested phrasings that work:**
- ✅ `arm the drone`
- ✅ `arm`
- ✅ `arm motors`
- ✅ `prepare for flight`

**May not work:**
- ❌ `arm drone` (missing "the")
- ❌ `ready to fly`

---

### 2. disarm()

**Tested phrasings that work:**
- ✅ `disarm the drone`
- ✅ `disarm`
- ✅ `disarm motors`

**May not work:**
- ❌ `disarm drone` (missing "the")

---

### 3. takeoff(altitude)

**Tested phrasings that work:**
- ✅ `takeoff to 15 meters`
- ✅ `take off to 10 meters`
- ✅ `takeoff to 20m`
- ✅ `take off at 15 meters`

**May not work:**
- ❌ `takeoff drone at 29` ← **This is your issue!**
- ❌ `fly up to 15 meters`
- ❌ `go up 10 meters`

**Why "takeoff drone at 29" doesn't work:**
The model was trained on patterns like "takeoff **to** X meters", not "takeoff drone **at** X". The word "to" is important!

**Solution:**
Use: `takeoff to 29 meters` or `take off to 29 meters`

---

### 4. land()

**Tested phrasings that work:**
- ✅ `land the drone`
- ✅ `land`
- ✅ `land now`

**May not work:**
- ❌ `land drone`
- ❌ `come down`

---

### 5. rtl() - Return to Launch

**Tested phrasings that work:**
- ✅ `return to launch`
- ✅ `return home`
- ✅ `RTL`
- ✅ `go home`

**May not work:**
- ❌ `return to base`
- ❌ `come back`

---

### 6. change_mode(mode)

**Tested phrasings that work:**
- ✅ `change mode to GUIDED`
- ✅ `switch to LOITER`
- ✅ `change mode to RTL`
- ✅ `set mode to LAND`

**Valid modes:**
- GUIDED
- LOITER
- RTL
- LAND
- STABILIZE
- ALT_HOLD

**May not work:**
- ❌ `change to GUIDED` (missing "mode")
- ❌ `mode GUIDED`

---

### 7. get_battery()

**Tested phrasings that work:**
- ✅ `check battery`
- ✅ `battery status`
- ✅ `what's the battery level`
- ✅ `battery health`

**Output format:**
```
🔋 Battery: 12.60V, 8.50A, 87% remaining
```

**May not work:**
- ❌ `how much battery`
- ❌ `battery percentage`

---

### 8. get_position()

**Tested phrasings that work:**
- ✅ `where am I`
- ✅ `get position`
- ✅ `current position`
- ✅ `what's my location`

**Output format:**
```
📍 Position: Lat -35.363262°, Lon 149.165237°, Alt 0.0m, Heading 354.6°
```

**May not work:**
- ❌ `where is the drone`
- ❌ `location`

---

## 🎓 Tips for Best Results

### 1. Use Complete Phrases
- ✅ `arm the drone` (complete)
- ❌ `arm drone` (incomplete)

### 2. Include Key Words
- For takeoff: Use "**to**" not "at"
- For mode: Include "**mode**"
- For battery: Include "**battery**"

### 3. Use Exact Numbers
- ✅ `takeoff to 15 meters`
- ✅ `takeoff to 15m`
- ✅ `takeoff to 15`

### 4. Common Patterns

**Pattern 1: Action + "the drone"**
```
arm the drone
disarm the drone
land the drone
```

**Pattern 2: Action + "to" + Value**
```
takeoff to 15 meters
change mode to GUIDED
```

**Pattern 3: Question Format**
```
where am I?
what's the battery level?
```

---

## 🔧 Troubleshooting

### Command Not Recognized

If your command isn't recognized:

1. **Check the phrasing** - Compare with working examples above
2. **Try simpler version** - Use basic form like "arm" instead of "arm the drone"
3. **Check spelling** - Make sure mode names are correct (GUIDED not GUIDE)
4. **Use numbers** - For altitude, use clear numbers: "15" not "fifteen"

### Example: Fixing Your Takeoff Issue

**Your command:**
```
takeoff drone at 29
```

**Why it failed:**
- Missing "the" before "drone"
- Using "at" instead of "to"
- Model wasn't trained on this pattern

**Fixed versions:**
```
✅ takeoff to 29 meters
✅ take off to 29 meters
✅ takeoff to 29m
✅ takeoff to 29
```

---

## 📊 Model Training Data Patterns

The Stage 1 model was trained on **206 examples** with these patterns:

| Function | Pattern | Example |
|----------|---------|---------|
| arm | `arm [the drone]` | "arm the drone" |
| takeoff | `takeoff to {altitude} [meters]` | "takeoff to 15 meters" |
| land | `land [the drone]` | "land the drone" |
| rtl | `return [to launch/home]` | "return to launch" |
| change_mode | `change mode to {mode}` | "change mode to GUIDED" |
| get_battery | `[check/get] battery [status]` | "check battery" |
| get_position | `where am I` / `get position` | "where am I" |

---

## 🚀 Stage 2 Improvements (Planned)

In Stage 2, we plan to improve natural language understanding:

- ✅ More flexible phrasing (e.g., "takeoff drone at X" will work)
- ✅ Synonyms (e.g., "fly up" = "takeoff")
- ✅ Context awareness (remembering previous commands)
- ✅ Multi-step commands (e.g., "arm and takeoff to 15 meters")

---

## 💡 Quick Reference Card

**Most Common Commands:**

```bash
# Basic Flight
arm the drone
takeoff to 15 meters
land the drone
return to launch

# Status Checks
check battery
where am I?

# Mode Changes
change mode to GUIDED
change mode to LOITER

# Disarm
disarm the drone
```

**Remember:** Use "**to**" for takeoff, not "at"!

---

## 📝 Adding New Phrasings

If you want to add new phrasings, you need to:

1. Add training examples to the training data
2. Retrain the model
3. Export to Ollama

See `TRAINING_GUIDE.md` for details on retraining.

---

**Last Updated:** 2025-12-26  
**Model Version:** ardupilot-stage1  
**Accuracy:** 85% (17/20 test cases)
