#!/usr/bin/env python3
"""
Test movement functionality for ArduPilot SITL

Tests arm, takeoff, and directional movement commands.
"""
from drone_functions import DroneController
import time

def main():
    print("=" * 50)
    print("ArduPilot Movement Test Script")
    print("=" * 50)

    drone = DroneController('udp:127.0.0.1:14550')

    print("\nConnecting to SITL...")
    if not drone.connect():
        print("Connection failed")
        return
    print("Connected")

    # Test 1: Get position
    print("\n--- Test 1: Get current position ---")
    result = drone.get_position()
    print(f"Result: {result}")

    # Test 1b: Switch to GUIDED mode (required for arming in SITL)
    print("\n--- Test 1b: Switch to GUIDED mode ---")
    result = drone.change_mode("GUIDED")
    print(f"Result: {result}")

    # Test 2: Arm
    print("\n--- Test 2: Arm the drone ---")
    result = drone.arm()
    print(f"Result: {result}")
    if result.get("status") != "success":
        print("Arming failed, cannot continue")
        return

    # Test 3: Takeoff
    print("\n--- Test 3: Takeoff to 10m ---")
    result = drone.takeoff(10)
    print(f"Result: {result}")
    if result.get("status") != "success":
        print("Takeoff failed")
        drone.disarm()
        return

    # Wait for takeoff
    print("\nWaiting 8 seconds for takeoff to complete...")
    time.sleep(8)

    # Test 4: Get position after takeoff
    print("\n--- Test 4: Get position after takeoff ---")
    result = drone.get_position()
    print(f"Result: {result}")
    alt = result.get("altitude", 0)
    print(f"Current altitude: {alt}m")

    # Test 5: Move west
    print("\n--- Test 5: Move west 5 meters ---")
    result = drone.move_west(5)
    print(f"Result: {result}")

    if result.get("status") == "success":
        print("MOVE WEST WORKS!")
        time.sleep(3)
    else:
        print(f"Move west failed: {result.get('message')}")

    # Test 6: Move east
    print("\n--- Test 6: Move east 5 meters ---")
    result = drone.move_east(5)
    print(f"Result: {result}")

    if result.get("status") == "success":
        print("MOVE EAST WORKS!")
        time.sleep(3)
    else:
        print(f"Move east failed: {result.get('message')}")

    # Test 7: Move north
    print("\n--- Test 7: Move north 5 meters ---")
    result = drone.move_north(5)
    print(f"Result: {result}")

    if result.get("status") == "success":
        print("MOVE NORTH WORKS!")
        time.sleep(3)
    else:
        print(f"Move north failed: {result.get('message')}")

    # Test 8: Move south
    print("\n--- Test 8: Move south 5 meters ---")
    result = drone.move_south(5)
    print(f"Result: {result}")

    if result.get("status") == "success":
        print("MOVE SOUTH WORKS!")
        time.sleep(3)
    else:
        print(f"Move south failed: {result.get('message')}")

    # Test 9: Increase altitude
    print("\n--- Test 9: Increase altitude by 5m ---")
    result = drone.increase_altitude(5)
    print(f"Result: {result}")

    if result.get("status") == "success":
        print("INCREASE ALTITUDE WORKS!")
        time.sleep(3)
    else:
        print(f"Increase altitude failed: {result.get('message')}")

    # Test 10: Land
    print("\n--- Test 10: Land ---")
    result = drone.land()
    print(f"Result: {result}")

    print("\n" + "=" * 50)
    print("Movement Test Complete")
    print("=" * 50)

if __name__ == "__main__":
    main()
