"""Test command dataset against ACTUAL LLM backend."""
import json
import sys
import requests
import time

BACKEND_URL = "http://localhost:5000"

def test_commands():
    # Check backend is running
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if r.status_code != 200:
            print("ERROR: Backend not healthy")
            sys.exit(1)
    except:
        print("ERROR: Backend not running. Start with: python run_server.py")
        sys.exit(1)

    with open('tests/command_test_dataset.json') as f:
        tests = json.load(f)

    print("="*70)
    print("COMMAND DATASET TEST - Live LLM Backend")
    print(f"Testing {len(tests)} commands against {BACKEND_URL}")
    print("="*70)

    PASS = 0
    FAIL = 0
    results = []

    for i, t in enumerate(tests):
        inp = t['input']
        expected = t['expected_tools']
        category = t.get('category', 'unknown')

        # Call actual backend
        try:
            r = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": inp, "mode": "agent"},
                timeout=30
            )
            data = r.json()
        except Exception as e:
            print(f"[{i+1}/{len(tests)}] ERROR: {inp[:30]}... - {e}")
            FAIL += 1
            continue

        # Extract what backend returned
        cmd = data.get('command')
        cmds = data.get('commands', [])

        # Build list of returned tool types
        returned_types = []
        if cmd:
            returned_types.append(cmd.get('type', ''))
        if cmds:
            for c in cmds:
                if c.get('type') and c.get('type') not in returned_types:
                    returned_types.append(c.get('type'))

        # Build expected types
        expected_types = []
        for e in (expected or []):
            tool = e.get('tool', '').lower()
            # Map tool name to command type
            type_map = {
                'arm': 'ARM', 'disarm': 'DISARM', 'takeoff': 'TAKEOFF',
                'land': 'LAND', 'rtl': 'RTL', 'move': 'MOVE_DIRECTION',
                'circle': 'CIRCLE', 'goto': 'GOTO', 'change_mode': 'CHANGE_MODE',
                'set_speed': 'SET_SPEED', 'set_altitude': 'ALTITUDE_CHANGE',
                'set_heading': 'SET_YAW', 'get_param': 'GET_PARAM',
                'set_param': 'SET_PARAM', 'search_param': 'SEARCH_PARAM',
                'get_status': 'GET_STATUS', 'get_position': 'GET_POSITION',
                'pause': 'PAUSE', 'hold': 'PAUSE', 'resume': 'RESUME',
                'explain_param': 'EXPLAIN_PARAM', 'reboot': 'REBOOT'
            }
            if tool in type_map:
                expected_types.append(type_map[tool])

        # Compare
        # For conversation/invalid, expect no command
        if not expected:
            if not cmd and not cmds:
                PASS += 1
                status = "PASS"
            else:
                FAIL += 1
                status = "FAIL"
                print(f"[{i+1}] FAIL [{category}]: '{inp[:40]}...'")
                print(f"     Expected: no command")
                print(f"     Got: {returned_types}")
        else:
            # Check if first expected matches first returned
            if returned_types and expected_types:
                if returned_types[0] == expected_types[0]:
                    PASS += 1
                    status = "PASS"
                else:
                    FAIL += 1
                    status = "FAIL"
                    print(f"[{i+1}] FAIL [{category}]: '{inp[:40]}...'")
                    print(f"     Expected: {expected_types}")
                    print(f"     Got: {returned_types}")
            elif not returned_types and expected_types:
                FAIL += 1
                status = "FAIL"
                print(f"[{i+1}] FAIL [{category}]: '{inp[:40]}...'")
                print(f"     Expected: {expected_types}")
                print(f"     Got: no command")
            else:
                FAIL += 1
                status = "FAIL"

        results.append({
            "input": inp,
            "category": category,
            "expected": expected_types,
            "got": returned_types,
            "status": status
        })

        # Progress
        if (i+1) % 10 == 0:
            print(f"Progress: {i+1}/{len(tests)} ({PASS} pass, {FAIL} fail)")

        # Small delay to not overwhelm LLM
        time.sleep(0.5)

    # Summary
    print(f"\n{'='*70}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {len(tests)} total")
    print(f"Accuracy: {PASS*100//len(tests)}%")
    print(f"{'='*70}")

    # Save detailed results
    with open('/tmp/command_test_results.json', 'w') as f:
        json.dump({"pass": PASS, "fail": FAIL, "total": len(tests), "details": results}, f, indent=2)
    print(f"Detailed results: /tmp/command_test_results.json")

    return FAIL == 0

if __name__ == "__main__":
    success = test_commands()
    sys.exit(0 if success else 1)
