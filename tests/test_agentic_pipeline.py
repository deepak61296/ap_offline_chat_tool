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


def run_case(results, name, message, expect_cmd=None, expect_no_cmd=False, mode="agent"):
    """Run a single test case."""
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
            results["pass"] += 1
        else:
            results["fail"] += 1
        
        results["items"].append({
            "test": name, "input": message, "expected": expect_cmd or "(none)",
            "got": cmd_type or "(none)", "passed": passed, "reason": reason,
            "response": ai
        })
        
        print(f"  {status} {name}")
        if not passed:
            print(f"     Expected: {expect_cmd}, Got: {cmd_type}")
            print(f"     AI: {ai}")
        
    except Exception as e:
        results["fail"] += 1
        results["items"].append({"test": name, "passed": False, "reason": str(e)})
        print(f"  ❌ {name} — ERROR: {e}")

def main():
    results = {"pass": 0, "fail": 0, "items": []}

    print("=" * 60)
    print("  ArduPilot AI Backend v3 — Test Suite")
    print("=" * 60)

    print("\n🔍 Health & Status")
    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        d = r.json()
        assert d["status"] == "healthy"
        results["pass"] += 1
        print("  ✅ Health check OK")
    except Exception as e:
        results["fail"] += 1
        print(f"  ❌ Health check FAILED: {e}")

    try:
        r = requests.get(f"{BASE}/status", timeout=5)
        d = r.json()
        assert d["status"] == "running"
        assert d["architecture"] == "agentic_v3_standalone_first"
        results["pass"] += 1
        print("  ✅ Status endpoint OK (agentic_v3)")
    except Exception as e:
        results["fail"] += 1
        print(f"  ❌ Status endpoint FAILED: {e}")

    print("\n🛩️  Basic Commands")
    run_case(results, "ARM", "arm the drone", expect_cmd="ARM")
    run_case(results, "DISARM", "disarm the drone", expect_cmd="DISARM")
    run_case(results, "TAKEOFF (auto-arms)", "takeoff to 25 meters", expect_cmd="ARM")
    run_case(results, "LAND", "land the drone", expect_cmd="LAND")
    run_case(results, "RTL", "return to launch", expect_cmd="RTL")

    print("\n🧭 Movement Commands")
    run_case(results, "Move North", "move north 50 meters", expect_cmd="MOVE_DIRECTION")
    run_case(results, "Move Forward", "move forward by 10m", expect_cmd="MOVE_DIRECTION")
    run_case(results, "Move Right", "move right 20m", expect_cmd="MOVE_DIRECTION")
    run_case(results, "Move Backward", "move backward 30m", expect_cmd="MOVE_DIRECTION")

    print("\n⚙️  Special Flows")
    run_case(results, "Circle", "circle drone 10m radius", expect_cmd="CHANGE_MODE")
    run_case(results, "Mode Change", "change mode to loiter", expect_cmd="CHANGE_MODE")

    print("\n🚨 Emergency")
    run_case(results, "Bring Back", "bring it back its dangerous", expect_cmd="RTL")
    run_case(results, "Abort", "abort abort!", expect_cmd="RTL")

    print("\n💬 Conversational (expect NO command)")
    run_case(results, "Greeting", "hello", expect_no_cmd=True)

    print("\n🗣️  Casual Language")
    run_case(results, "Casual Arm", "arm it", expect_cmd="ARM")
    run_case(results, "Come Home", "come home", expect_cmd="RTL")
    run_case(results, "Go Up", "go up 15 meters", expect_cmd="ALTITUDE_CHANGE")

    print("\n🔗 Multi-Step Missions")
    run_case(results, "Arm+Takeoff", "arm the drone and takeoff to 20m", expect_cmd="ARM")

    print("\n📊 Parameters")
    run_case(results, "Get Param", "what is BATT_CAPACITY", expect_cmd="GET_PARAM")

    print("\n🎯 Speed & Heading")
    run_case(results, "Set Speed", "set speed to 5 m/s", expect_cmd="SET_SPEED")

    print("\n📖 Ask Mode (never returns commands)")
    run_case(results, "Ask Mode", "what flight modes does ArduPilot support?", expect_no_cmd=True, mode="ask")

    print("\n" + "=" * 60)
    total = results["pass"] + results["fail"]
    print(f"  RESULTS: {results['pass']} passed, {results['fail']} failed, {total} total")
    print("=" * 60)

    with open("/tmp/test_results.json", "w") as f:
        json.dump(
            {"passed": results["pass"], "failed": results["fail"], "total": total, "tests": results["items"]},
            f,
            indent=2,
        )

    print("\nDetailed results saved to /tmp/test_results.json")
    sys.exit(1 if results["fail"] > 0 else 0)


if __name__ == "__main__":
    main()
