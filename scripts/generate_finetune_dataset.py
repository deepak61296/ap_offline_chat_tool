#!/usr/bin/env python3
"""
ArduPilot AI Dataset Generator
Procedurally generates a massive fine-tuning dataset formatted exactly for Unsloth / Qwen 3.5.
Outputs a ChatML-compliant `.jsonl` file to train the model on exact regex-matching phrases.
"""

import json
import random
import os

OUTPUT_FILE = "qwen_finetune_dataset.jsonl"
NUM_EXAMPLES = 2000

# The exact system prompt the model will see in production
SYSTEM_PROMPT = "You are an AI assistant for ArduPilot Mission Planner with COMMAND EXECUTION capabilities. Be helpful but SAFE. Only execute when explicitly asked."

# --- TELEMETRY GENERATORS ---
def generate_telemetry():
    return {
        "battery": {
            "voltage": round(random.uniform(10.5, 16.8), 1),
            "remaining": random.randint(5, 100)
        },
        "gps": {
            "satellites": random.randint(0, 22),
            "latitude": round(random.uniform(-90.0, 90.0), 5),
            "longitude": round(random.uniform(-180.0, 180.0), 5),
            "altitude": round(random.uniform(0.0, 100.0), 1)
        },
        "status": {
            "mode": random.choice(["STABILIZE", "LOITER", "GUIDED", "AUTO", "RTL"]),
            "armed": random.choice([True, False])
        }
    }

def format_telemetry_prompt(telem):
    return (f"CONNECTION STATUS: Connected\n\n"
            f"--- CURRENT TELEMETRY ---\n"
            f"Battery: {telem['battery']['voltage']}V ({telem['battery']['remaining']}%)\n"
            f"GPS: {telem['gps']['satellites']} sats | Lat: {telem['gps']['latitude']} | Lon: {telem['gps']['longitude']}\n"
            f"Altitude: {telem['gps']['altitude']}m\n"
            f"Mode: {telem['status']['mode']} | Armed: {telem['status']['armed']}\n"
            f"-------------------------")

# --- COMMAND DICTIONARY (USER PHRASING -> EXACT ASSISTANT OUTPUT) ---
# Assistant outputs MUST match backend/commands.py regex exactly.

COMMAND_TEMPLATES = [
    # ARM
    ({"arm the drone", "spin up the motors", "arm", "start motors"}, "Arming the drone now."),
    # DISARM
    ({"disarm", "kill the motors", "stop motors", "shut down engines"}, "Disarming the drone."),
    # TAKEOFF
    ({"take off to {x} meters", "takeoff to {x}m", "fly up to {x} meters", "ascend to {x}"}, "Taking off to {x} meters."),
    # LAND
    ({"land", "land the drone", "bring it down", "EMERGENCY LAND NOW", "stop and land"}, "Landing the drone."),
    # RTL
    ({"rtl", "return to launch", "come home", "bring it home", "ABORT ABORT"}, "Returning to launch."),
    # MOVE
    ({"move {dir} {x} meters", "fly {dir} for {x}m", "go {dir} {x} meters", "head {dir} {x}m"}, "Moving {dir} {x} meters."),
    # ALTITUDE
    ({"increase altitude by {x} meters", "go up {x}m", "climb {x} meters"}, "Increasing altitude by {x} meters."),
    ({"decrease altitude by {x} meters", "go down {x}m", "drop {x} meters"}, "Decreasing altitude by {x} meters."),
    # MODES
    ({"change mode to {mode}", "switch to {mode}", "set flight mode to {mode}"}, "Changing mode to {mode}."),
    # SPEED
    ({"set speed to {v} m/s", "fly at {v} m/s", "change speed to {v}"}, "Setting speed to {v} m/s."),
    # NEW COMMAND: ORBIT
    ({"orbit here at {x} meters", "circle around this location at {x}m radius", "do an orbit at {x}m"}, "Orbiting current location at {x} meters radius."),
    # NEW COMMAND: BRAKE
    ({"brake", "stop moving", "hold position", "halt!"}, "Braking immediately."),
    # NEW COMMAND: SMART RTL
    ({"smart rtl", "return safely via smart rtl"}, "Returning to launch via safe path."),
    # NEW COMMAND: SEARCH PARAM
    ({"how do I change my {param}?", "what parameter controls {param}?", "search for params related to {param}"}, "Searching for parameter related to {param}."),
    # REJECT DIAGONALS
    ({"move northeast {x}m", "fly southwest {x} meters"}, "I can only move in cardinal directions: north, south, east, or west. Please specify one of these directions."),
    # VAGUE TAKEOFF (REJECTION)
    ({"i want to takeoff", "can we takeoff?"}, "Would you like me to takeoff? Please confirm the altitude.")
]

# Randomizing variables
DIRECTIONS = ["north", "south", "east", "west"]
MODES = ["GUIDED", "AUTO", "LOITER", "STABILIZE"]
PARAMS = ["speed", "tilt", "battery failsafe", "tuning", "fences"]

def generate_row():
    # 1. Pick a random command template
    input_options, exact_output = random.choice(COMMAND_TEMPLATES)
    user_input = random.choice(list(input_options))
    
    # 2. Fill parameters
    x = random.randint(5, 100)
    v = random.randint(1, 15)
    direction = random.choice(DIRECTIONS)
    mode = random.choice(MODES)
    param = random.choice(PARAMS)
    
    user_input = user_input.replace("{x}", str(x)).replace("{v}", str(v)).replace("{dir}", direction).replace("{mode}", mode).replace("{param}", param)
    exact_output = exact_output.replace("{x}", str(x)).replace("{v}", str(v)).replace("{dir}", direction).replace("{mode}", mode).replace("{param}", param)
    
    # 3. Add typos occasionally to user input for robustness
    if random.random() < 0.1:
        user_input = user_input.replace("meters", "mters").replace("takeoff", "take of").replace("land", "lnad")

    # 4. Generate Telemetry
    telem = generate_telemetry()
    full_user_prompt = f"{user_input}\n\n{format_telemetry_prompt(telem)}"
    
    # 5. Build ChatML format
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_user_prompt},
            {"role": "assistant", "content": exact_output}
        ]
    }

def main():
    print(f"Generating {NUM_EXAMPLES} highly-varied dataset examples...")
    dataset = []
    
    for _ in range(NUM_EXAMPLES):
        dataset.append(generate_row())
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for row in dataset:
            f.write(json.dumps(row) + "\n")
            
    print(f"✅ Created {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB)")
    print(f"Ready for Unsloth / Qwen 3.5 Fine-Tuning!")

if __name__ == "__main__":
    main()
