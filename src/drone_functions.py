"""
ArduPilot Drone Control Functions Library
Provides function definitions for FunctionGemma to call via PyMAVLink
"""

from pymavlink import mavutil
from typing import Optional, Dict, Any
import time

class DroneController:
    """PyMAVLink-based drone controller for ArduCopter"""
    
    def __init__(self, connection_string: str = 'udp:127.0.0.1:14550'):
        """
        Initialize connection to drone/SITL
        
        Args:
            connection_string: MAVLink connection string (default: SITL UDP)
        """
        self.master = None
        self.connection_string = connection_string
        self.mission_items = []  # Store mission waypoints
        self.mission_mode = False  # Track if building mission
        
    def connect(self) -> bool:
        """
        Connect to the drone
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self.master = mavutil.mavlink_connection(self.connection_string)
            # Wait for heartbeat
            self.master.wait_heartbeat()
            print(f"✅ Connected to drone (sysid={self.master.target_system}, compid={self.master.target_component})")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def _check_armed_state(self) -> bool:
        """
        Helper method to reliably check if the drone is armed.

        This method receives a HEARTBEAT message and checks the armed flag
        in base_mode. This is more reliable than motors_armed() in SITL
        because it ensures we have fresh state from the vehicle.

        Returns:
            True if armed, False otherwise
        """
        try:
            # Receive a fresh HEARTBEAT to get current state
            msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
            if msg:
                # Check the armed flag in base_mode
                return bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            return False
        except:
            return False

    def arm(self) -> Dict[str, Any]:
        """
        Arm the drone motors

        Returns:
            Dictionary with status and message
        """
        try:
            # Check if already armed by receiving fresh HEARTBEAT
            if self._check_armed_state():
                return {"status": "success", "message": "Drone is already armed"}

            # Send arm command using MAV_CMD_COMPONENT_ARM_DISARM
            # This is more reliable than arducopter_arm() as it gives us COMMAND_ACK
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # confirmation
                1,  # param1: 1 = arm, 0 = disarm
                0,  # param2: 0 = arm normally, 21196 = force arm (bypasses checks)
                0, 0, 0, 0, 0  # params 3-7 (unused)
            )

            # Wait for COMMAND_ACK first
            ack = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack:
                if ack.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                    if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                        # Arming was rejected - get reason from result code
                        result_names = {
                            0: "Accepted",
                            1: "Temporarily rejected",
                            2: "Denied",
                            3: "Unsupported",
                            4: "Failed",
                            5: "In progress",
                            6: "Cancelled"
                        }
                        reason = result_names.get(ack.result, f"Unknown ({ack.result})")
                        return {"status": "error", "message": f"Arming rejected: {reason}"}

            # Wait for arming confirmation via HEARTBEAT
            # The COMMAND_ACK means command was accepted, but we verify armed state
            arm_start = time.time()
            while time.time() - arm_start < 5:  # 5 second timeout
                msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=0.5)
                if msg:
                    # Check armed flag in base_mode
                    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
                        return {"status": "success", "message": "Drone armed successfully"}
                time.sleep(0.1)

            return {"status": "error", "message": "Arming timeout - check pre-arm failures"}

        except Exception as e:
            return {"status": "error", "message": f"Failed to arm: {str(e)}"}
    
    def disarm(self) -> Dict[str, Any]:
        """
        Disarm the drone motors

        Returns:
            Dictionary with status and message
        """
        try:
            # Check if already disarmed
            if not self._check_armed_state():
                return {"status": "success", "message": "Drone is already disarmed"}

            # Send disarm command using MAV_CMD_COMPONENT_ARM_DISARM
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # confirmation
                0,  # param1: 0 = disarm
                0,  # param2
                0, 0, 0, 0, 0  # params 3-7 (unused)
            )

            # Wait for COMMAND_ACK
            ack = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack:
                if ack.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                    if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                        return {"status": "error", "message": "Disarm command rejected"}

            # Wait for disarm confirmation via HEARTBEAT
            disarm_start = time.time()
            while time.time() - disarm_start < 5:
                msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=0.5)
                if msg:
                    if not (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
                        return {"status": "success", "message": "Drone disarmed successfully"}
                time.sleep(0.1)

            return {"status": "error", "message": "Disarm timeout"}

        except Exception as e:
            return {"status": "error", "message": f"Failed to disarm: {str(e)}"}
    
    def takeoff(self, altitude: float) -> Dict[str, Any]:
        """
        Take off to specified altitude

        Args:
            altitude: Target altitude in meters (relative to home)

        Returns:
            Dictionary with status and message
        """
        try:
            # Validation
            if altitude < 2:
                return {"status": "error", "message": "Takeoff altitude too low (minimum 2m)"}
            if altitude > 120:
                return {"status": "error", "message": "Takeoff altitude too high (maximum 120m)"}

            # Check if armed using reliable HEARTBEAT-based detection
            if not self._check_armed_state():
                return {
                    "status": "error",
                    "message": "Drone must be armed first. Use 'arm' command."
                }
            
            # Check current mode
            mode_info = self.get_mode()
            if mode_info.get("status") == "success":
                current_mode = mode_info.get("mode")
                # Takeoff works in GUIDED and AUTO modes
                if current_mode not in ["GUIDED", "AUTO"]:
                    return {
                        "status": "error",
                        "message": f"Drone is in {current_mode} mode. Takeoff requires GUIDED mode. Should I switch to GUIDED mode?",
                        "current_mode": current_mode,
                        "needs_mode_change": True
                    }
            
            # Change to GUIDED mode if not already
            current_mode = mode_info.get("mode", "")
            if current_mode != "GUIDED":
                mode_result = self.change_mode("GUIDED")
                if mode_result.get("status") != "success":
                    return {"status": "error", "message": "Failed to switch to GUIDED mode"}
            
            # Send takeoff command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0,  # confirmation
                0, 0, 0, 0,  # params 1-4
                0, 0,  # param 5-6 (lat, lon)
                altitude  # param 7 (altitude)
            )
            
            # Wait for ACK
            ack = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == 0:
                return {
                    "status": "success", 
                    "message": f"Taking off to {altitude}m",
                    "altitude": altitude
                }
            else:
                return {"status": "error", "message": "Takeoff command rejected"}
        except Exception as e:
            return {"status": "error", "message": f"Takeoff failed: {str(e)}"}
    
    def land(self) -> Dict[str, Any]:
        """
        Land the drone at current location
        
        Returns:
            Dictionary with status and message
        """
        try:
            # Change to LAND mode
            self.change_mode("LAND")
            return {"status": "success", "message": "Landing initiated"}
        except Exception as e:
            return {"status": "error", "message": f"Landing failed: {str(e)}"}
    
    def rtl(self) -> Dict[str, Any]:
        """
        Return to launch (home) position
        
        Returns:
            Dictionary with status and message
        """
        try:
            self.change_mode("RTL")
            return {"status": "success", "message": "Returning to launch"}
        except Exception as e:
            return {"status": "error", "message": f"RTL failed: {str(e)}"}
    
    def change_mode(self, mode: str) -> Dict[str, Any]:
        """
        Change flight mode
        
        Args:
            mode: Flight mode name (GUIDED, LAND, RTL, LOITER, etc.)
        
        Returns:
            Dictionary with status and message
        """
        try:
            # Get mode ID
            mode_id = self.master.mode_mapping()[mode]
            
            # Send mode change command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                0,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id,
                0, 0, 0, 0, 0
            )
            
            # Wait for ACK
            ack = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == 0:
                return {"status": "success", "message": f"Mode changed to {mode}"}
            else:
                return {"status": "error", "message": f"Mode change to {mode} rejected"}
        except Exception as e:
            return {"status": "error", "message": f"Mode change failed: {str(e)}"}
    
    def goto_location(self, lat: float, lon: float, alt: float) -> Dict[str, Any]:
        """
        Go to specified GPS location
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            alt: Altitude in meters (relative to home)
        
        Returns:
            Dictionary with status and message
        """
        try:
            # Ensure in GUIDED mode
            self.change_mode("GUIDED")
            
            # Send position target
            self.master.mav.mission_item_send(
                self.master.target_system,
                self.master.target_component,
                0,  # seq
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                2,  # current (2 = guided mode target)
                0,  # autocontinue
                0, 0, 0, 0,  # params 1-4
                lat, lon, alt
            )
            
            return {
                "status": "success",
                "message": f"Flying to lat={lat}, lon={lon}, alt={alt}m",
                "latitude": lat,
                "longitude": lon,
                "altitude": alt
            }
        except Exception as e:
            return {"status": "error", "message": f"Goto failed: {str(e)}"}
    
    def set_speed(self, speed: float, speed_type: str = "ground") -> Dict[str, Any]:
        """
        Set vehicle speed
        
        Args:
            speed: Speed in m/s
            speed_type: Type of speed ('ground' or 'air')
        
        Returns:
            Dictionary with status and message
        """
        try:
            speed_type_val = 1 if speed_type == "ground" else 0
            
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,
                0,
                speed_type_val,  # speed type
                speed,  # speed (m/s)
                -1,  # throttle (no change)
                0, 0, 0, 0
            )
            
            ack = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == 0:
                return {
                    "status": "success",
                    "message": f"{speed_type.capitalize()} speed set to {speed} m/s"
                }
            else:
                return {"status": "error", "message": "Speed change rejected"}
        except Exception as e:
            return {"status": "error", "message": f"Speed change failed: {str(e)}"}
    
    def get_position(self) -> Dict[str, Any]:
        """
        Get current drone position

        Returns:
            Dictionary with latitude, longitude, altitude, and heading
        """
        try:
            # Request position data by sending a message request
            # This ensures SITL sends us fresh GLOBAL_POSITION_INT data
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_POSITION,
                2,  # rate Hz
                1   # start
            )

            # Try to get GLOBAL_POSITION_INT message with retries
            for _ in range(3):
                msg = self.master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=2)
                if msg:
                    return {
                        "status": "success",
                        "latitude": msg.lat / 1e7,
                        "longitude": msg.lon / 1e7,
                        "altitude": msg.relative_alt / 1000.0,  # Convert from mm to m
                        "heading": msg.hdg / 100.0  # Convert from centidegrees
                    }

            return {"status": "error", "message": "Position data not available"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get position: {str(e)}"}
    
    def get_current_altitude(self) -> float:
        """Get current altitude in meters, returns -1 on error"""
        try:
            pos = self.get_position()
            if pos.get("status") == "success":
                return pos["altitude"]
            return -1
        except:
            return -1
    
    def get_mode(self) -> Dict[str, Any]:
        """
        Get current flight mode
        
        Returns:
            Dictionary with current mode name
        """
        try:
            msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=3)
            if msg:
                # Get mode from custom_mode field
                mode_id = msg.custom_mode
                mode_mapping_inv = {v: k for k, v in self.master.mode_mapping().items()}
                mode_name = mode_mapping_inv.get(mode_id, "UNKNOWN")
                
                return {
                    "status": "success",
                    "mode": mode_name,
                    "mode_id": mode_id
                }
            else:
                return {"status": "error", "message": "Cannot get mode"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get mode: {str(e)}"}
    
    def is_armable(self) -> Dict[str, Any]:
        """
        Check if drone is ready to arm
        
        Returns:
            Dictionary with armable status and reasons
        """
        try:
            msg = self.master.recv_match(type='SYS_STATUS', blocking=True, timeout=3)
            if not msg:
                return {"status": "error", "message": "Cannot get system status"}
            
            # Check sensors health (onboard_control_sensors_health)
            sensors_ok = (msg.onboard_control_sensors_health & 
                         msg.onboard_control_sensors_enabled) == msg.onboard_control_sensors_enabled
            
            issues = []
            
            # Check GPS
            gps_msg = self.master.recv_match(type='GPS_RAW_INT', blocking=True, timeout=1)
            if gps_msg:
                if gps_msg.fix_type < 3:  # Less than 3D fix
                    issues.append("GPS fix not adequate (need 3D fix)")
            else:
                issues.append("No GPS data")
            
            # Check battery
            if msg.voltage_battery < 10000:  # Less than 10V (mV)
                issues.append("Battery voltage too low")
            
            # Check if already armed using reliable HEARTBEAT-based detection
            if self._check_armed_state():
                return {
                    "status": "success",
                    "armable": False,
                    "reason": "Already armed"
                }
            
            if issues:
                return {
                    "status": "success",
                    "armable": False,
                    "issues": issues,
                    "message": "Pre-arm checks failed: " + ", ".join(issues)
                }
            
            return {
                "status": "success",
                "armable": True,
                "message": "Ready to arm"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check armable status: {str(e)}"
            }
    
    def get_battery(self) -> Dict[str, Any]:
        """
        Get battery status
        
        Returns:
            Dictionary with battery voltage, current, and remaining percentage
        """
        try:
            msg = self.master.recv_match(type='SYS_STATUS', blocking=True, timeout=3)
            
            if msg:
                return {
                    "status": "success",
                    "voltage": msg.voltage_battery / 1000.0,  # Convert from mV to V
                    "current": msg.current_battery / 100.0,  # Convert from cA to A
                    "remaining": msg.battery_remaining  # Percentage
                }
            else:
                return {"status": "error", "message": "Battery data not available"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get battery: {str(e)}"}
    
    def increase_altitude(self, meters: float) -> Dict[str, Any]:
        """
        Increase altitude by specified meters (relative to current altitude)

        Args:
            meters: Meters to climb (must be positive)

        Returns:
            Dictionary with status and message
        """
        try:
            # Validation
            if meters <= 0:
                return {"status": "error", "message": "Altitude increase must be positive"}

            if meters > 100:
                return {"status": "error", "message": "Altitude increase too large (max 100m at once)"}

            # Check if armed
            if not self._check_armed_state():
                return {"status": "error", "message": "Vehicle must be armed"}

            # Get current altitude with retries
            current_alt = self.get_current_altitude()
            if current_alt < 0:
                return {"status": "error", "message": "Cannot get current altitude - position data unavailable"}

            if current_alt < 0.5:
                return {"status": "error", "message": "Vehicle not airborne, use takeoff command"}
            
            target_alt = current_alt + meters
            
            # Send position target with new altitude
            self.change_mode("GUIDED")
            
            msg = self.master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=3)
            if not msg:
                return {"status": "error", "message": "Cannot get current position"}
            
            self.master.mav.mission_item_send(
                self.master.target_system,
                self.master.target_component,
                0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                2,  # current
                0,  # autocontinue
                0, 0, 0, 0,
                msg.lat / 1e7,
                msg.lon / 1e7,
                target_alt
            )
            
            return {
                "status": "success",
                "message": f"Climbing {meters}m to {target_alt}m",
                "current_altitude": current_alt,
                "target_altitude": target_alt
            }
        except Exception as e:
            return {"status": "error", "message": f"Altitude increase failed: {str(e)}"}
    
    def decrease_altitude(self, meters: float) -> Dict[str, Any]:
        """
        Decrease altitude by specified meters (relative to current altitude)

        Args:
            meters: Meters to descend (must be positive)

        Returns:
            Dictionary with status and message
        """
        try:
            # Validation
            if meters <= 0:
                return {"status": "error", "message": "Altitude decrease must be positive"}

            # Check if armed
            if not self._check_armed_state():
                return {"status": "error", "message": "Vehicle must be armed"}

            # Get current altitude
            current_alt = self.get_current_altitude()
            if current_alt < 0:
                return {"status": "error", "message": "Cannot get current altitude - position data unavailable"}

            if current_alt < 0.5:
                return {"status": "error", "message": "Already on ground"}
            
            target_alt = current_alt - meters
            
            # Safety check - don't go below 1 meter
            if target_alt < 1.0:
                return {
                    "status": "error", 
                    "message": f"Target altitude {target_alt:.1f}m too low, use land command instead"
                }
            
            # Send position target with new altitude
            self.change_mode("GUIDED")
            
            msg = self.master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=3)
            if not msg:
                return {"status": "error", "message": "Cannot get current position"}
            
            self.master.mav.mission_item_send(
                self.master.target_system,
                self.master.target_component,
                0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                2,  # current
                0,  # autocontinue
                0, 0, 0, 0,
                msg.lat / 1e7,
                msg.lon / 1e7,
                target_alt
            )
            
            return {
                "status": "success",
                "message": f"Descending {meters}m to {target_alt}m",
                "current_altitude": current_alt,
                "target_altitude": target_alt
            }
        except Exception as e:
            return {"status": "error", "message": f"Altitude decrease failed: {str(e)}"}
    
    def move_north(self, meters: float) -> Dict[str, Any]:
        """Move north by specified meters"""
        return self.move_relative(north=meters, east=0, down=0)
    
    def move_south(self, meters: float) -> Dict[str, Any]:
        """Move south by specified meters"""
        return self.move_relative(north=-meters, east=0, down=0)
    
    def move_east(self, meters: float) -> Dict[str, Any]:
        """Move east by specified meters"""
        return self.move_relative(north=0, east=meters, down=0)
    
    def move_west(self, meters: float) -> Dict[str, Any]:
        """Move west by specified meters"""
        return self.move_relative(north=0, east=-meters, down=0)
    
    def move_relative(self, north: float, east: float, down: float) -> Dict[str, Any]:
        """
        Move relative to current position in NED (North-East-Down) frame

        Args:
            north: Meters north (negative for south)
            east: Meters east (negative for west)
            down: Meters down (negative for up)

        Returns:
            Dictionary with status and message
        """
        try:
            # Validation
            if abs(north) > 1000 or abs(east) > 1000:
                return {"status": "error", "message": "Movement distance too large (max 1000m)"}

            # Check if armed first (must be armed for any movement)
            if not self._check_armed_state():
                return {"status": "error", "message": "Vehicle must be armed for movement"}

            # Check if airborne by getting altitude
            current_alt = self.get_current_altitude()
            if current_alt < 0:
                # Could not get altitude, check if we might still be flying
                # by verifying we're armed and in a flying mode
                mode_info = self.get_mode()
                current_mode = mode_info.get("mode", "")
                if current_mode not in ["GUIDED", "AUTO", "LOITER", "POSHOLD"]:
                    return {"status": "error", "message": "Cannot get altitude. Ensure vehicle is in GUIDED mode."}
                # If armed and in flight mode, proceed cautiously
            elif current_alt < 0.5:
                return {"status": "error", "message": "Vehicle must be airborne for relative movement. Use takeoff first."}

            # Ensure in GUIDED mode
            self.change_mode("GUIDED")
            
            # Send SET_POSITION_TARGET_LOCAL_NED
            self.master.mav.set_position_target_local_ned_send(
                0,  # time_boot_ms
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,
                0b0000111111111000,  # type_mask (only positions enabled)
                north, east, down,
                0, 0, 0,  # vx, vy, vz
                0, 0, 0,  # afx, afy, afz
                0, 0  # yaw, yaw_rate
            )
            
            direction = []
            if north > 0: direction.append(f"{north}m north")
            elif north < 0: direction.append(f"{abs(north)}m south")
            if east > 0: direction.append(f"{east}m east")
            elif east < 0: direction.append(f"{abs(east)}m west")
            if down > 0: direction.append(f"{down}m down")
            elif down < 0: direction.append(f"{abs(down)}m up")
            
            direction_str = ", ".join(direction) if direction else "no movement"
            
            return {
                "status": "success",
                "message": f"Moving {direction_str}",
                "north": north,
                "east": east,
                "down": down
            }
        except Exception as e:
            return {"status": "error", "message": f"Relative movement failed: {str(e)}"}
    
    def create_mission(self) -> Dict[str, Any]:
        """
        Start creating a new mission (clears existing mission items)
        
        Returns:
            Dictionary with status and message
        """
        self.mission_items = []
        self.mission_mode = True
        return {
            "status": "success",
            "message": "Mission creation started. Add waypoints with add_waypoint command."
        }
    
    def add_takeoff_waypoint(self, altitude: float) -> Dict[str, Any]:
        """
        Add takeoff waypoint to mission
        
        Args:
            altitude: Takeoff altitude in meters
        
        Returns:
            Dictionary with status and message
        """
        if not self.mission_mode:
            return {"status": "error", "message": "Call create_mission first"}
        
        if altitude < 2 or altitude > 120:
            return {"status": "error", "message": "Takeoff altitude must be 2-120m"}
        
        # Takeoff waypoint
        waypoint = {
            "seq": len(self.mission_items),
            "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            "command": mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0,
            "x": 0, "y": 0, "z": altitude
        }
        self.mission_items.append(waypoint)
        
        return {
            "status": "success",
            "message": f"Added takeoff to {altitude}m (waypoint #{len(self.mission_items)})"
        }
    
    def add_waypoint(self, lat: float, lon: float, alt: float) -> Dict[str, Any]:
        """
        Add waypoint to mission
        
        Args:
            lat: Latitude in degrees (or 0 to use current)
            lon: Longitude in degrees (or 0 to use current)
            alt: Altitude in meters
        
        Returns:
            Dictionary with status and message
        """
        if not self.mission_mode:
            return {"status": "error", "message": "Call create_mission first"}
        
        # Validation
        if alt < 1 or alt > 500:
            return {"status": "error", "message": "Altitude must be 1-500m"}
        
        waypoint = {
            "seq": len(self.mission_items),
            "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            "command": mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0,
            "x": lat, "y": lon, "z": alt
        }
        self.mission_items.append(waypoint)
        
        return {
            "status": "success",
            "message": f"Added waypoint at ({lat}, {lon}, {alt}m) - waypoint #{len(self.mission_items)}"
        }
    
    def add_relative_waypoint(self, north: float, east: float, alt: float) -> Dict[str, Any]:
        """
        Add waypoint relative to current/home position
        
        Args:
            north: Meters north from home
            east: Meters east from home
            alt: Altitude in meters
        
        Returns:
            Dictionary with status and message
        """
        if not self.mission_mode:
            return {"status": "error", "message": "Call create_mission first"}
        
        waypoint = {
            "seq": len(self.mission_items),
            "frame": mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            "command": mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0,
            "x": north, "y": east, "z": -alt  # NED uses down as positive
        }
        self.mission_items.append(waypoint)
        
        return {
            "status": "success",
            "message": f"Added relative waypoint ({north}m N, {east}m E, {alt}m alt) - waypoint #{len(self.mission_items)}"
        }
    
    def add_land_waypoint(self) -> Dict[str, Any]:
        """
        Add land waypoint to mission
        
        Returns:
            Dictionary with status and message
        """
        if not self.mission_mode:
            return {"status": "error", "message": "Call create_mission first"}
        
        waypoint = {
            "seq": len(self.mission_items),
            "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            "command": mavutil.mavlink.MAV_CMD_NAV_LAND,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0,
            "x": 0, "y": 0, "z": 0
        }
        self.mission_items.append(waypoint)
        
        return {
            "status": "success",
            "message": f"Added land waypoint - waypoint #{len(self.mission_items)}"
        }
    
    def get_mission_summary(self) -> Dict[str, Any]:
        """
        Get summary of current mission
        
        Returns:
            Dictionary with mission details
        """
        if not self.mission_items:
            return {"status": "error", "message": "No mission items"}
        
        summary = []
        for i, wp in enumerate(self.mission_items):
            cmd = wp["command"]
            if cmd == mavutil.mavlink.MAV_CMD_NAV_TAKEOFF:
                summary.append(f"{i+1}. Takeoff to {wp['z']}m")
            elif cmd == mavutil.mavlink.MAV_CMD_NAV_WAYPOINT:
                if wp['frame'] == mavutil.mavlink.MAV_FRAME_LOCAL_NED:
                    summary.append(f"{i+1}. Go to ({wp['x']}m N, {wp['y']}m E, {-wp['z']}m alt)")
                else:
                    summary.append(f"{i+1}. Go to ({wp['x']}, {wp['y']}, {wp['z']}m)")
            elif cmd == mavutil.mavlink.MAV_CMD_NAV_LAND:
                summary.append(f"{i+1}. Land")
        
        return {
            "status": "success",
            "waypoint_count": len(self.mission_items),
            "summary": "\n".join(summary)
        }
    
    def upload_mission(self) -> Dict[str, Any]:
        """
        Upload mission to vehicle
        
        Returns:
            Dictionary with status and message
        """
        if not self.mission_items:
            return {"status": "error", "message": "No mission to upload"}
        
        try:
            # Clear existing mission
            self.master.mav.mission_clear_all_send(
                self.master.target_system,
                self.master.target_component
            )
            
            # Wait for ACK
            ack = self.master.recv_match(type='MISSION_ACK', blocking=True, timeout=3)
            
            # Send mission count
            self.master.mav.mission_count_send(
                self.master.target_system,
                self.master.target_component,
                len(self.mission_items)
            )
            
            # Upload each waypoint
            for wp in self.mission_items:
                # Wait for mission request
                msg = self.master.recv_match(type='MISSION_REQUEST', blocking=True, timeout=3)
                if not msg:
                    return {"status": "error", "message": "Timeout waiting for mission request"}
                
                # Send waypoint
                self.master.mav.mission_item_send(
                    self.master.target_system,
                    self.master.target_component,
                    wp["seq"],
                    wp["frame"],
                    wp["command"],
                    0,  # current
                    1,  # autocontinue
                    wp["param1"], wp["param2"], wp["param3"], wp["param4"],
                    wp["x"], wp["y"], wp["z"]
                )
            
            # Wait for final ACK
            ack = self.master.recv_match(type='MISSION_ACK', blocking=True, timeout=3)
            if ack and ack.type == 0:
                return {
                    "status": "success",
                    "message": f"Mission uploaded successfully ({len(self.mission_items)} waypoints)"
                }
            else:
                return {"status": "error", "message": "Mission upload failed"}
                
        except Exception as e:
            return {"status": "error", "message": f"Mission upload failed: {str(e)}"}
    
    def start_mission(self) -> Dict[str, Any]:
        """
        Start executing uploaded mission (change to AUTO mode)
        
        Returns:
            Dictionary with status and message
        """
        try:
            self.change_mode("AUTO")
            return {
                "status": "success",
                "message": "Mission started (AUTO mode)"
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to start mission: {str(e)}"}
    
    def clear_mission(self) -> Dict[str, Any]:
        """
        Clear current mission (local buffer only)
        
        Returns:
            Dictionary with status and message
        """
        self.mission_items = []
        self.mission_mode = False
        return {
            "status": "success",
            "message": "Mission cleared"
        }
    
    def arm_and_takeoff(self, altitude: float) -> Dict[str, Any]:
        """
        Composite function: Arm motors and takeoff to altitude in one command
        
        Args:
            altitude: Target altitude in meters
            
        Returns:
            Dictionary with status and message
        """
        try:
            if altitude < 2 or altitude > 120:
                return {"status": "error", "message": "Altitude must be 2-120m"}
            
            # Arm
            arm_result = self.arm()
            if arm_result.get("status") != "success":
                return arm_result
            
            time.sleep(0.5)
            
            # Takeoff
            takeoff_result = self.takeoff(altitude)
            return takeoff_result
        except Exception as e:
            return {"status": "error", "message": f"Arm and takeoff failed: {str(e)}"}
    
    def hover(self, duration: float) -> Dict[str, Any]:
        """Hold current position for specified duration in seconds"""
        try:
            if duration <= 0 or duration > 300:
                return {"status": "error", "message": "Duration must be 0-300 seconds"}
            
            if not self._check_armed_state():
                return {"status": "error", "message": "Vehicle must be armed"}
            
            self.change_mode("LOITER")
            time.sleep(duration)
            
            return {"status": "success", "message": f"Hovered for {duration} seconds"}
        except Exception as e:
            return {"status": "error", "message": f"Hover failed: {str(e)}"}
    
    def land_and_disarm(self) -> Dict[str, Any]:
        """Composite function: Land and automatically disarm"""
        try:
            land_result = self.land()
            if land_result.get("status") != "success":
                return land_result
            
            # Wait for landing
            time.sleep(10)
            
            disarm_result = self.disarm()
            return {"status": "success", "message": "Landed and disarmed"}
        except Exception as e:
            return {"status": "error", "message": f"Land and disarm failed: {str(e)}"}
    
    def set_parameter(self, param_name: str, value: float) -> Dict[str, Any]:
        """Set ArduPilot parameter (e.g., 'WPNAV_SPEED', 500)"""
        try:
            param_id = param_name.encode('utf-8')[:16]
            
            self.master.mav.param_set_send(
                self.master.target_system,
                self.master.target_component,
                param_id,
                value,
                mavutil.mavlink.MAV_PARAM_TYPE_REAL32
            )
            
            ack = self.master.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
            if ack:
                return {"status": "success", "message": f"Parameter {param_name} set to {value}"}
            else:
                return {"status": "error", "message": f"Failed to set {param_name}"}
        except Exception as e:
            return {"status": "error", "message": f"Parameter set failed: {str(e)}"}
    
    def get_parameter(self, param_name: str) -> Dict[str, Any]:
        """Get ArduPilot parameter value"""
        try:
            param_id = param_name.encode('utf-8')[:16]
            
            self.master.mav.param_request_read_send(
                self.master.target_system,
                self.master.target_component,
                param_id,
                -1
            )
            
            response = self.master.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
            if response:
                return {
                    "status": "success",
                    "parameter": param_name,
                    "value": response.param_value
                }
            else:
                return {"status": "error", "message": f"Parameter {param_name} not found"}
        except Exception as e:
            return {"status": "error", "message": f"Parameter get failed: {str(e)}"}
    
    def emergency_stop(self) -> Dict[str, Any]:
        """Emergency motor stop - USE WITH CAUTION! Drone will fall."""
        try:
            self.disarm()
            return {"status": "success", "message": "EMERGENCY STOP executed"}
        except Exception as e:
            return {"status": "error", "message": f"Emergency stop failed: {str(e)}"}
    
    def set_yaw(self, angle: float, relative: bool = False) -> Dict[str, Any]:
        """Set drone heading/yaw in degrees (0-360)"""
        try:
            self.change_mode("GUIDED")
            
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                angle,
                0,
                1 if angle >= 0 else -1,
                1 if relative else 0,
                0, 0, 0
            )
            
            ack = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == 0:
                return {"status": "success", "message": f"Yaw set to {angle}°"}
            else:
                return {"status": "error", "message": "Yaw command rejected"}
        except Exception as e:
            return {"status": "error", "message": f"Set yaw failed: {str(e)}"}


# Function definitions for FunctionGemma
# These will be provided to the model in the proper format

DRONE_FUNCTIONS = {
    "arm": {
        "name": "arm",
        "description": "Arm the drone motors to prepare for flight. The drone must be armed before takeoff.",
        "parameters": {}
    },
    "disarm": {
        "name": "disarm",
        "description": "Disarm the drone motors. This should be done after landing.",
        "parameters": {}
    },
    "takeoff": {
        "name": "takeoff",
        "description": "Take off to a specified altitude. The drone must be armed first.",
        "parameters": {
            "altitude": {
                "type": "number",
                "description": "Target altitude in meters (relative to home/launch position)",
                "required": True
            }
        }
    },
    "land": {
        "name": "land",
        "description": "Land the drone at its current location",
        "parameters": {}
    },
    "rtl": {
        "name": "rtl",
        "description": "Return to launch position. Makes the drone fly back to where it took off and land.",
        "parameters": {}
    },
    "change_mode": {
        "name": "change_mode",
        "description": "Change the flight mode of the drone. Common modes: GUIDED, LOITER, RTL, LAND, STABILIZE, AUTO.",
        "parameters": {
            "mode": {
                "type": "string",
                "description": "Flight mode name (GUIDED, LOITER, RTL, LAND, STABILIZE, AUTO, etc.)",
                "required": True
            }
        }
    },
    "goto_location": {
        "name": "goto_location",
        "description": "Fly to a specific GPS location at a given altitude",
        "parameters": {
            "lat": {
                "type": "number",
                "description": "Latitude in degrees",
                "required": True
            },
            "lon": {
                "type": "number",
                "description": "Longitude in degrees",
                "required": True
            },
            "alt": {
                "type": "number",
                "description": "Altitude in meters (relative to home)",
                "required": True
            }
        }
    },
    "set_speed": {
        "name": "set_speed",
        "description": "Set the vehicle's speed",
        "parameters": {
            "speed": {
                "type": "number",
                "description": "Speed in meters per second",
                "required": True
            },
            "speed_type": {
                "type": "string",
                "description": "Type of speed: 'ground' or 'air'",
                "required": False
            }
        }
    },
    "get_position": {
        "name": "get_position",
        "description": "Get the current GPS position and altitude of the drone",
        "parameters": {}
    },
    "get_battery": {
        "name": "get_battery",
        "description": "Get the current battery status including voltage, current, and remaining percentage",
        "parameters": {}
    },
    "get_mode": {
        "name": "get_mode",
        "description": "Get the current flight mode of the drone",
        "parameters": {}
    },
    "is_armable": {
        "name": "is_armable",
        "description": "Check if the drone is ready to arm (pre-arm checks)",
        "parameters": {}
    },
    "increase_altitude": {
        "name": "increase_altitude",
        "description": "Increase altitude by specified meters. Use when drone is already flying and you want to go higher.",
        "parameters": {
            "meters": {
                "type": "number",
                "description": "Meters to climb (positive number, max 100m)",
                "required": True
            }
        }
    },
    "decrease_altitude": {
        "name": "decrease_altitude",
        "description": "Decrease altitude by specified meters. Use when drone is flying and you want to descend but not land.",
        "parameters": {
            "meters": {
                "type": "number",
                "description": "Meters to descend (positive number)",
                "required": True
            }
        }
    },
    "move_north": {
        "name": "move_north",
        "description": "Move north by specified meters while maintaining altitude",
        "parameters": {
            "meters": {
                "type": "number",
                "description": "Meters to move north",
                "required": True
            }
        }
    },
    "move_south": {
        "name": "move_south",
        "description": "Move south by specified meters while maintaining altitude",
        "parameters": {
            "meters": {
                "type": "number",
                "description": "Meters to move south",
                "required": True
            }
        }
    },
    "move_east": {
        "name": "move_east",
        "description": "Move east by specified meters while maintaining altitude",
        "parameters": {
            "meters": {
                "type": "number",
                "description": "Meters to move east",
                "required": True
            }
        }
    },
    "move_west": {
        "name": "move_west",
        "description": "Move west by specified meters while maintaining altitude",
        "parameters": {
            "meters": {
                "type": "number",
                "description": "Meters to move west",
                "required": True
            }
        }
    },
    "create_mission": {
        "name": "create_mission",
        "description": "Start creating a new mission plan. This clears any existing mission and allows you to add waypoints.",
        "parameters": {}
    },
    "add_takeoff_waypoint": {
        "name": "add_takeoff_waypoint",
        "description": "Add a takeoff waypoint to the mission at specified altitude",
        "parameters": {
            "altitude": {
                "type": "number",
                "description": "Takeoff altitude in meters (2-120m)",
                "required": True
            }
        }
    },
    "add_waypoint": {
        "name": "add_waypoint",
        "description": "Add a GPS waypoint to the mission",
        "parameters": {
            "lat": {
                "type": "number",
                "description": "Latitude in degrees",
                "required": True
            },
            "lon": {
                "type": "number",
                "description": "Longitude in degrees",
                "required": True
            },
            "alt": {
                "type": "number",
                "description": "Altitude in meters",
                "required": True
            }
        }
    },
    "add_relative_waypoint": {
        "name": "add_relative_waypoint",
        "description": "Add a waypoint relative to home position (useful for simple missions like 'go north 10m')",
        "parameters": {
            "north": {
                "type": "number",
                "description": "Meters north from home (negative for south)",
                "required": True
            },
            "east": {
                "type": "number",
                "description": "Meters east from home (negative for west)",
                "required": True
            },
            "alt": {
                "type": "number",
                "description": "Altitude in meters",
                "required": True
            }
        }
    },
    "add_land_waypoint": {
        "name": "add_land_waypoint",
        "description": "Add a land command to the mission",
        "parameters": {}
    },
    "get_mission_summary": {
        "name": "get_mission_summary",
        "description": "Get a summary of the current mission plan",
        "parameters": {}
    },
    "upload_mission": {
        "name": "upload_mission",
        "description": "Upload the created mission to the drone",
        "parameters": {}
    },
    "start_mission": {
        "name": "start_mission",
        "description": "Start executing the uploaded mission (switches to AUTO mode)",
        "parameters": {}
    },
    "clear_mission": {
        "name": "clear_mission",
        "description": "Clear the current mission plan",
        "parameters": {}
    },
    "arm_and_takeoff": {
        "name": "arm_and_takeoff",
        "description": "Arm motors and takeoff to altitude in one command. Combines arm() and takeoff().",
        "parameters": {
            "altitude": {
                "type": "number",
                "description": "Target altitude in meters (2-120m)",
                "required": True
            }
        }
    },
    "hover": {
        "name": "hover",
        "description": "Hold current position for specified duration. Useful for waiting or pausing.",
        "parameters": {
            "duration": {
                "type": "number",
                "description": "Time to hover in seconds (max 300)",
                "required": True
            }
        }
    },
    "land_and_disarm": {
        "name": "land_and_disarm",
        "description": "Land and automatically disarm motors. Combines land() and disarm().",
        "parameters": {}
    },
    "set_parameter": {
        "name": "set_parameter",
        "description": "Set ArduPilot parameter value. Examples: WPNAV_SPEED, RTL_ALT, ANGLE_MAX",
        "parameters": {
            "param_name": {
                "type": "string",
                "description": "Parameter name (e.g., 'WPNAV_SPEED')",
                "required": True
            },
            "value": {
                "type": "number",
                "description": "Parameter value",
                "required": True
            }
        }
    },
    "get_parameter": {
        "name": "get_parameter",
        "description": "Get ArduPilot parameter value",
        "parameters": {
            "param_name": {
                "type": "string",
                "description": "Parameter name to retrieve",
                "required": True
            }
        }
    },
    "emergency_stop": {
        "name": "emergency_stop",
        "description": "EMERGENCY ONLY: Immediately stop motors. Drone will fall. Use only in critical situations.",
        "parameters": {}
    },
    "set_yaw": {
        "name": "set_yaw",
        "description": "Set drone heading/yaw angle",
        "parameters": {
            "angle": {
                "type": "number",
                "description": "Target angle in degrees (0-360)",
                "required": True
            },
            "relative": {
                "type": "boolean",
                "description": "If true, angle is relative to current heading",
                "required": False
            }
        }
    }
}