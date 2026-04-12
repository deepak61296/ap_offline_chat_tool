"""Test parameter dataset against ACTUAL LLM backend."""
import json
import sys
import requests
import time

BACKEND_URL = "http://localhost:5000"

def test_param_search():
    # Check backend is running
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if r.status_code != 200:
            print("ERROR: Backend not healthy")
            sys.exit(1)
    except:
        print("ERROR: Backend not running. Start with: python run_server.py")
        sys.exit(1)

    with open('tests/param_test_dataset.json') as f:
        tests = json.load(f)

    print("="*70)
    print("PARAMETER DATASET TEST - Live LLM Backend")
    print(f"Testing {len(tests)} queries against {BACKEND_URL}")
    print("="*70)

    PASS = 0
    PARTIAL = 0
    FAIL = 0
    results = []

    for i, t in enumerate(tests):
        query = t['query']
        expected = t['expected_params']
        category = t.get('category', 'unknown')

        # Call actual backend
        try:
            r = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": query, "mode": "agent"},
                timeout=30
            )
            data = r.json()
        except Exception as e:
            print(f"[{i+1}/{len(tests)}] ERROR: {query[:30]}... - {e}")
            FAIL += 1
            continue

        response = data.get('response', '')

        # Check if expected params are mentioned in response
        if not expected:
            # Expect no params found
            if 'no param' in response.lower() or 'not found' in response.lower() or len(response) < 50:
                PASS += 1
                status = "PASS"
            else:
                # Check if any real param names appear
                has_param = any(p in response.upper() for p in ['BATT_', 'MOT_', 'GPS_', 'RTL_', 'FENCE_'])
                if has_param:
                    FAIL += 1
                    status = "FAIL"
                    print(f"[{i+1}] FAIL [{category}]: '{query[:40]}...'")
                    print(f"     Expected: no params")
                    print(f"     Response mentioned params")
                else:
                    PASS += 1
                    status = "PASS"
        else:
            # Check if expected params are mentioned in response
            hits = [p for p in expected if p in response.upper()]

            if len(hits) >= 1:
                PASS += 1
                status = "PASS"
            else:
                # Check if at least the category is addressed
                category_keywords = {
                    'battery': ['BATT', 'BATTERY', 'VOLTAGE'],
                    'motor': ['MOT', 'MOTOR', 'SPIN'],
                    'gps': ['GPS', 'SATELLITE'],
                    'failsafe': ['FAILSAFE', 'FS_', 'FAIL'],
                    'navigation': ['WPNAV', 'SPEED', 'NAV'],
                    'arming': ['ARM', 'DISARM'],
                }
                cat_keys = category_keywords.get(category, [])
                if any(k in response.upper() for k in cat_keys):
                    PARTIAL += 1
                    status = "PARTIAL"
                    print(f"[{i+1}] PARTIAL [{category}]: '{query[:40]}...'")
                    print(f"     Expected: {expected}")
                    print(f"     Got category match but not exact param")
                else:
                    FAIL += 1
                    status = "FAIL"
                    print(f"[{i+1}] FAIL [{category}]: '{query[:40]}...'")
                    print(f"     Expected: {expected}")
                    print(f"     Response: {response[:100]}...")

        results.append({
            "query": query,
            "category": category,
            "expected": expected,
            "response_snippet": response[:200],
            "status": status
        })

        # Progress
        if (i+1) % 10 == 0:
            print(f"Progress: {i+1}/{len(tests)} ({PASS} pass, {PARTIAL} partial, {FAIL} fail)")

        # Small delay
        time.sleep(0.5)

    # Summary
    total = PASS + PARTIAL + FAIL
    print(f"\n{'='*70}")
    print(f"RESULTS: {PASS} passed, {PARTIAL} partial, {FAIL} failed, {total} total")
    print(f"Accuracy: {PASS*100//total}% perfect, {(PASS+PARTIAL)*100//total}% acceptable")
    print(f"{'='*70}")

    # Save detailed results
    with open('/tmp/param_test_results.json', 'w') as f:
        json.dump({"pass": PASS, "partial": PARTIAL, "fail": FAIL, "total": total, "details": results}, f, indent=2)
    print(f"Detailed results: /tmp/param_test_results.json")

    return FAIL == 0

if __name__ == "__main__":
    success = test_param_search()
    sys.exit(0 if success else 1)
