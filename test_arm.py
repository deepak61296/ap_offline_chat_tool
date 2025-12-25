#!/usr/bin/env python3
"""
Test arming functionality for ArduPilot SITL

This script tests the fixed arm/disarm functions to verify
that arming detection works correctly with SITL.
"""
from drone_functions import DroneController
import time

def main():
    print("=" * 50)
    print("ArduPilot Arming Test Script")
    print("=" * 50)

    drone = DroneController('udp:127.0.0.1:14550')

    print("\nConnecting to SITL...")
    if not drone.connect():
        print("Connection failed")
        return
    print("Connected")

    # Test 1: Check if armable
    print("\n--- Test 1: Check if armable ---")
    result = drone.is_armable()
    print(f"Result: {result}")

    # Test 2: Get current mode
    print("\n--- Test 2: Get current mode ---")
    result = drone.get_mode()
    print(f"Result: {result}")

    # Test 3: Check armed state before arming
    print("\n--- Test 3: Check armed state (should be False) ---")
    armed = drone._check_armed_state()
    print(f"Armed: {armed}")

    # Test 4: Arm the drone
    print("\n--- Test 4: Arm the drone ---")
    result = drone.arm()
    print(f"Result: {result}")

    if result.get("status") == "success":
        print("ARMING WORKS!")

        # Test 5: Check armed state after arming
        print("\n--- Test 5: Check armed state after 2 seconds ---")
        time.sleep(2)
        armed = drone._check_armed_state()
        print(f"Armed: {armed}")

        if armed:
            print("Armed state detection confirmed!")
        else:
            print("WARNING: Armed state not detected correctly")

        # Test 6: Try to arm again (should say already armed)
        print("\n--- Test 6: Try to arm again (should say already armed) ---")
        result = drone.arm()
        print(f"Result: {result}")

        # Test 7: Disarm
        print("\n--- Test 7: Disarm ---")
        result = drone.disarm()
        print(f"Result: {result}")

        if result.get("status") == "success":
            print("DISARMING WORKS!")

            # Test 8: Check disarmed state
            print("\n--- Test 8: Check armed state after disarm ---")
            time.sleep(1)
            armed = drone._check_armed_state()
            print(f"Armed: {armed}")

            if not armed:
                print("Disarmed state detection confirmed!")
        else:
            print("DISARMING FAILED")
    else:
        print("ARMING FAILED")
        print("Debug info:")
        print(f"  - Check SITL console for pre-arm errors")
        print(f"  - Make sure SITL is in a mode that allows arming (GUIDED, LOITER, etc.)")

    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)

if __name__ == "__main__":
    main()
