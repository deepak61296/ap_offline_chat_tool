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
    
    def arm(self) -> Dict[str, Any]:
        """
        Arm the drone motors
        
        Returns:
            Dictionary with status and message
        """
        try:
            self.master.arducopter_arm()
            self.master.motors_armed_wait()
            return {"status": "success", "message": "Drone armed successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to arm: {str(e)}"}
    
    def disarm(self) -> Dict[str, Any]:
        """
        Disarm the drone motors
        
        Returns:
            Dictionary with status and message
        """
        try:
            self.master.arducopter_disarm()
            self.master.motors_disarmed_wait()
            return {"status": "success", "message": "Drone disarmed successfully"}
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
            # Change to GUIDED mode first
            self.change_mode("GUIDED")
            
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
            # Request GLOBAL_POSITION_INT message
            msg = self.master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=3)
            
            if msg:
                return {
                    "status": "success",
                    "latitude": msg.lat / 1e7,
                    "longitude": msg.lon / 1e7,
                    "altitude": msg.relative_alt / 1000.0,  # Convert from mm to m
                    "heading": msg.hdg / 100.0  # Convert from centidegrees
                }
            else:
                return {"status": "error", "message": "Position data not available"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get position: {str(e)}"}
    
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
        "description": "Change the flight mode of the drone. Common modes: GUIDED, LOITER, RTL, LAND, STABILIZE.",
        "parameters": {
            "mode": {
                "type": "string",
                "description": "Flight mode name (GUIDED, LOITER, RTL, LAND, STABILIZE, etc.)",
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
    }
}
