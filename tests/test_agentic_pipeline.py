#!/usr/bin/env python3
"""
Comprehensive test suite for the Agentic Pipeline v3.
Tests the full Planner → Executor → QGC pipeline via HTTP.
"""

import requests
import json
import sys
import time

BASE = "http://localhost:5000"
PASS = 0
FAIL = 0
RESULTS = []

def test(name, message, expect_cmd=None, expect_no_cmd=False, mode="agent"):
    """Run a single test case."""
    global PASS, FAIL
    try:
        r = requests.post(f"{BASE}/chat", json={"message": message, "mode": mode}, timeout=60)
        d = r.json()
        
        cmd = d.get("command")
        cmd_type = cmd.get("type") if cmd else None
        ai = (d.get("response") or "")[:120]
        
        passed = True
        reason = ""
        
        if expect_no_cmd:
            if cmd is not None:
                passed = False
                reason = f"Expected no command, got {cmd_type}"
        elif expect_cmd:
            if cmd_type != expect_cmd:
                passed = False
                reason = f"Expected {expect_cmd}, got {cmd_type}"
        
        status = "✅" if passed else "❌"
        if passed:
            PASS += 1
        else:
            FAIL += 1
        
        RESULTS.append({
            "test": name, "input": message, "expected": expect_cmd or "(none)",
            "got": cmd_type or "(none)", "passed": passed, "reason": reason,
            "response": ai
        })
        
        print(f"  {status} {name}")
        if not passed:
            print(f"     Expected: {expect_cmd}, Got: {cmd_type}")
            print(f"     AI: {ai}")
        
    except Exception as e:
        FAIL += 1
        RESULTS.append({"test": name, "passed": False, "reason": str(e)})
        print(f"  ❌ {name} — ERROR: {e}")


print("=" * 60)
print("  ArduPilot AI Backend v3 — Test Suite")
print("=" * 60)

# ─── Health Check ───
print("\n🔍 Health & Status")
try:
    r = requests.get(f"{BASE}/health", timeout=5)
    d = r.json()
    assert d["status"] == "healthy"
    assert d["version"] == "3.0.0"
    PASS += 1
    print("  ✅ Health check OK")
except Exception as e:
    FAIL += 1
    print(f"  ❌ Health check FAILED: {e}")

try:
    r = requests.get(f"{BASE}/status", timeout=5)
    d = r.json()
    assert d["status"] == "running"
    assert d["architecture"] == "agentic_v3"
    PASS += 1
    print("  ✅ Status endpoint OK (agentic_v3)")
except Exception as e:
    FAIL += 1
    print(f"  ❌ Status endpoint FAILED: {e}")

# ─── Basic Commands ───
print("\n🛩️  Basic Commands")
test("ARM", "arm the drone", expect_cmd="ARM")
test("DISARM", "disarm the drone", expect_cmd="DISARM")
test("TAKEOFF (auto-arms)", "takeoff to 25 meters", expect_cmd="ARM")  # Smart: auto-prepends ARM first
test("LAND", "land the drone", expect_cmd="LAND")
test("RTL", "return to launch", expect_cmd="RTL")

# ─── Movement ───
print("\n🧭 Movement Commands")
test("Move North", "move north 50 meters", expect_cmd="MOVE_DIRECTION")
test("Move Forward", "move forward by 10m", expect_cmd="MOVE_DIRECTION")
test("Move Right", "move right 20m", expect_cmd="MOVE_DIRECTION")
test("Move Backward", "move backward 30m", expect_cmd="MOVE_DIRECTION")

# ─── Special Flows ───
print("\n⚙️  Special Flows")
test("Circle", "circle drone 10m radius", expect_cmd="CHANGE_MODE")
test("Mode Change", "change mode to loiter", expect_cmd="CHANGE_MODE")

# ─── Emergency ───
print("\n🚨 Emergency")
test("Bring Back", "bring it back its dangerous", expect_cmd="RTL")
test("Abort", "abort abort!", expect_cmd="RTL")

# ─── Conversational (No Command) ───
print("\n💬 Conversational (expect NO command)")
test("Greeting", "hello", expect_no_cmd=True)

# ─── Casual Language ───
print("\n🗣️  Casual Language")
test("Casual Arm", "arm it", expect_cmd="ARM")
test("Come Home", "come home", expect_cmd="RTL")
test("Go Up", "go up 15 meters", expect_cmd="ALTITUDE_CHANGE")

# ─── Multi-Step ───
print("\n🔗 Multi-Step Missions")
test("Arm+Takeoff", "arm the drone and takeoff to 20m", expect_cmd="ARM")  # First in sequence

# ─── Parameters ───
print("\n📊 Parameters")
test("Get Param", "what is BATT_CAPACITY", expect_cmd="GET_PARAM")

# ─── Speed & Heading ───
print("\n🎯 Speed & Heading")
test("Set Speed", "set speed to 5 m/s", expect_cmd="SET_SPEED")

# ─── Ask Mode ───
print("\n📖 Ask Mode (never returns commands)")
test("Ask Mode", "what flight modes does ArduPilot support?", expect_no_cmd=True, mode="ask")

# ─── Summary ───
print("\n" + "=" * 60)
print(f"  RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
print("=" * 60)

# Save results
with open("/tmp/test_results.json", "w") as f:
    json.dump({"passed": PASS, "failed": FAIL, "total": PASS + FAIL, "tests": RESULTS}, f, indent=2)

print(f"\nDetailed results saved to /tmp/test_results.json")
sys.exit(1 if FAIL > 0 else 0)
