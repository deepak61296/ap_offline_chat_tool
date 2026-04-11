# Interview Prep: ArduPilot AI Backend

## 10 Technical Questions & Answers

### 1. Why did you choose regex-based command extraction instead of letting the LLM output structured JSON?

The LLM outputs natural language responses like "Arming the drone now." We extract commands using regex patterns that match these specific phrases. This is more reliable than asking the LLM to output JSON because: (a) smaller models often produce malformed JSON, (b) we can enforce exact phrase matching which prevents false positives, and (c) it lets us show the user a natural response while still extracting the command programmatically.

### 2. How do you handle the case where a user says something ambiguous like "go up" without specifying distance?

The system prompt instructs the LLM to ask for clarification when parameters are missing. For example, "go up" without a distance should prompt "How many meters would you like to go up?" The command extraction only triggers on complete phrases like "Increasing altitude by X meters" - partial commands don't match our regex patterns, so no command gets executed.

### 3. What's the purpose of the template injection system for Lua scripts?

Template injection bypasses the LLM entirely for common script requests. We have 31 pre-written, tested Lua templates (battery monitor, GPS alert, auto-RTL, etc.). When a user asks "create a battery monitor script", we pattern-match to a template and fill in parameters. This is faster, more reliable, and produces guaranteed-working code. The LLM only generates scripts for novel requests that don't match templates.

### 4. How does your test suite validate command extraction accuracy?

We have 170+ tests across 12 categories: baseline commands, natural language variations, typos, ambiguous inputs, compound requests, and safety-critical scenarios. Each test sends a message to the backend and validates the extracted command type matches expectations. Tests include adversarial cases like "can you arm?" (should NOT arm, just explain) vs "arm the drone" (should arm).

### 5. What safety mechanisms prevent dangerous commands from executing?

Three layers: (1) Validation limits in config.py - max takeoff altitude 500m, max movement distance 1000m, max GOTO distance 10km. (2) Risk classification - commands are tagged low/medium/high/critical risk, and the GCS can require confirmation for high-risk commands. (3) Prompt engineering - the LLM is instructed to only execute on explicit direct commands, not questions or indirect requests like "I want to arm."

### 6. Why does the command extraction check only the first line for basic commands like ARM/DISARM?

This prevents false positives from multi-line responses. If the LLM says "Arming the drone now. Make sure the area is clear before takeoff.", we only want to extract ARM, not accidentally trigger something from the second sentence. For commands with parameters (takeoff altitude, movement distance), we search the full response because the parameter might appear later.

### 7. How does the Lua post-processor fix common LLM mistakes?

LLMs often generate incorrect ArduPilot Lua API calls. The post-processor has regex replacements for common errors: `vehicle:set_mode("RTL")` becomes `vehicle:set_mode(6)` (modes are numbers, not strings), `battery:get_voltage()` becomes `battery:voltage(0)` (correct API with instance parameter), `ahrs:num_sats()` becomes `gps:num_sats(0)` (GPS is not in AHRS). This catches about 80% of API mistakes automatically.

### 8. What's the difference between Agent, Ask, and Script modes?

Agent mode executes commands - it can arm, takeoff, move the drone. Ask mode is read-only - it answers questions about telemetry but refuses to execute commands, saying "switch to Agent mode to execute commands." Script mode generates Lua scripts for the flight controller. Each mode has a different system prompt that constrains the LLM's behavior and output format.

### 9. How do you handle GCS integration across Mission Planner, MAVProxy, and QGroundControl?

The backend is a standalone Flask server that exposes HTTP endpoints. Each GCS has a custom integration: MAVProxy has a Python module that intercepts console input and sends it to /chat, Mission Planner has a C# plugin with a chat panel, QGC has a QML-based chat widget. All integrations use the same /chat endpoint and handle command execution themselves via MAVLink.

### 10. What failure modes did you discover during testing and how did you address them?

Key failures: (1) LLM would arm when user asked "can you arm?" - fixed by adding explicit rules in the prompt distinguishing questions from commands. (2) "move north 50m" was sometimes interpreted as GOTO coordinates - fixed by checking first line only and ordering extraction by specificity. (3) Mode changes sometimes triggered arm - fixed by making extraction patterns mutually exclusive. (4) Diagonal directions (northeast) crashed - fixed by rejecting non-cardinal directions with a clear error message.
