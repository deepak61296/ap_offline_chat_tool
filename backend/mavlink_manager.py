"""
MAVLink Connection Manager
Direct connection to ArduPilot via pymavlink
Works standalone or alongside any GCS (Mission Planner, MAVProxy, QGC)

Cross-platform: Windows and Linux compatible
"""

import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import pymavlink (optional dependency)
try:
    from pymavlink import mavutil
    PYMAVLINK_AVAILABLE = True
except ImportError:
    PYMAVLINK_AVAILABLE = False
    logger.warning("pymavlink not installed. Standalone mode unavailable.")


class ConnectionState(Enum):
    """MAVLink connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class TelemetryData:
    """Current telemetry state"""
    # Battery
    battery_voltage: float = 0.0
    battery_current: float = 0.0
    battery_remaining: int = 0

    # GPS
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    altitude_msl: float = 0.0
    satellites: int = 0
    fix_type: int = 0
    hdop: float = 0.0

    # Attitude
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    # Speed
    ground_speed: float = 0.0
    air_speed: float = 0.0
    climb_rate: float = 0.0

    # Status
    mode: str = "UNKNOWN"
    armed: bool = False
    system_status: int = 0

    # Home
    home_lat: float = 0.0
    home_lon: float = 0.0
    home_alt: float = 0.0

    # Timestamps
    last_heartbeat: float = 0.0
    last_update: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "battery": {
                "voltage": round(self.battery_voltage, 2),
                "current": round(self.battery_current, 2),
                "remaining": self.battery_remaining
            },
            "gps": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "altitude": round(self.altitude, 1),
                "altitude_msl": round(self.altitude_msl, 1),
                "satellites": self.satellites,
                "fix_type": self._fix_type_str(),
                "hdop": round(self.hdop, 2)
            },
            "attitude": {
                "roll": round(self.roll, 1),
                "pitch": round(self.pitch, 1),
                "yaw": round(self.yaw, 1)
            },
            "speed": {
                "ground_speed": round(self.ground_speed, 1),
                "air_speed": round(self.air_speed, 1),
                "climb_rate": round(self.climb_rate, 1)
            },
            "status": {
                "mode": self.mode,
                "armed": self.armed,
                "system_status": self._system_status_str()
            },
            "home": {
                "latitude": self.home_lat,
                "longitude": self.home_lon,
                "altitude": round(self.home_alt, 1)
            }
        }

    def _fix_type_str(self) -> str:
        """Convert GPS fix type to string"""
        fix_types = {0: "NO_FIX", 1: "NO_FIX", 2: "2D", 3: "3D", 4: "DGPS", 5: "RTK_FLOAT", 6: "RTK_FIXED"}
        return fix_types.get(self.fix_type, "UNKNOWN")

    def _system_status_str(self) -> str:
        """Convert system status to string"""
        statuses = {0: "UNINIT", 1: "BOOT", 2: "CALIBRATING", 3: "STANDBY", 4: "ACTIVE", 5: "CRITICAL", 6: "EMERGENCY"}
        return statuses.get(self.system_status, "UNKNOWN")


@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class MAVLinkManager:
    """
    MAVLink connection manager for direct vehicle communication

    Usage:
        manager = MAVLinkManager()
        manager.connect("tcp:127.0.0.1:5760")  # SITL
        manager.connect("udp:127.0.0.1:14550") # MAVProxy
        manager.connect("/dev/ttyUSB0")        # Serial (Linux)
        manager.connect("COM3")                # Serial (Windows)
    """

    # ArduPilot flight modes (Copter)
    COPTER_MODES = {
        0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO", 4: "GUIDED",
        5: "LOITER", 6: "RTL", 7: "CIRCLE", 8: "POSITION", 9: "LAND",
        10: "OF_LOITER", 11: "DRIFT", 12: "SPORT", 13: "FLIP", 14: "AUTOTUNE",
        15: "POSHOLD", 16: "BRAKE", 17: "THROW", 18: "AVOID_ADSB", 19: "GUIDED_NOGPS",
        20: "SMART_RTL", 21: "FLOWHOLD", 22: "FOLLOW", 23: "ZIGZAG", 24: "SYSTEMID",
        25: "AUTOROTATE", 26: "AUTO_RTL"
    }

    # Reverse mapping for mode names to numbers
    COPTER_MODE_NUMBERS = {v: k for k, v in COPTER_MODES.items()}

    def __init__(self):
        self._connection = None
        self._state = ConnectionState.DISCONNECTED
        self._telemetry = TelemetryData()
        self._running = False
        self._recv_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[TelemetryData], None]] = []
        self._lock = threading.Lock()
        self._connection_string = ""

    @property
    def state(self) -> ConnectionState:
        """Get current connection state"""
        return self._state

    @property
    def connected(self) -> bool:
        """Check if connected to vehicle"""
        return self._state == ConnectionState.CONNECTED

    @property
    def telemetry(self) -> TelemetryData:
        """Get current telemetry data"""
        with self._lock:
            return self._telemetry

    def connect(self, connection_string: str, baud: int = 57600) -> bool:
        """
        Connect to vehicle via MAVLink

        Args:
            connection_string: Connection string
                - TCP: "tcp:127.0.0.1:5760"
                - UDP: "udp:127.0.0.1:14550"
                - Serial Linux: "/dev/ttyUSB0" or "/dev/ttyACM0"
                - Serial Windows: "COM3"
            baud: Baud rate for serial connections (default 57600)

        Returns:
            True if connection successful
        """
        if not PYMAVLINK_AVAILABLE:
            logger.error("pymavlink not installed. Run: pip install pymavlink")
            self._state = ConnectionState.ERROR
            return False

        if self.connected:
            logger.warning("Already connected. Disconnect first.")
            return False

        self._state = ConnectionState.CONNECTING
        self._connection_string = connection_string

        try:
            logger.info(f"Connecting to {connection_string}...")

            # Create MAVLink connection
            self._connection = mavutil.mavlink_connection(
                connection_string,
                baud=baud,
                source_system=255,  # GCS system ID
                source_component=0
            )

            # Wait for heartbeat
            logger.info("Waiting for heartbeat...")
            msg = self._connection.wait_heartbeat(timeout=10)

            if msg is None:
                logger.error("No heartbeat received")
                self._state = ConnectionState.ERROR
                return False

            logger.info(f"Heartbeat received from system {self._connection.target_system}")

            # Request data streams
            self._request_data_streams()

            # Start receive thread
            self._running = True
            self._recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._recv_thread.start()

            self._state = ConnectionState.CONNECTED
            logger.info(f"Connected to vehicle at {connection_string}")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._state = ConnectionState.ERROR
            return False

    def disconnect(self) -> bool:
        """Disconnect from vehicle"""
        self._running = False

        if self._recv_thread and self._recv_thread.is_alive():
            self._recv_thread.join(timeout=2)

        if self._connection:
            self._connection.close()
            self._connection = None

        self._state = ConnectionState.DISCONNECTED
        logger.info("Disconnected from vehicle")
        return True

    def _request_data_streams(self):
        """Request telemetry data streams from vehicle"""
        if not self._connection:
            return

        # Request all data streams at 4Hz
        self._connection.mav.request_data_stream_send(
            self._connection.target_system,
            self._connection.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL,
            4,  # 4 Hz
            1   # Start
        )

    def _receive_loop(self):
        """Background thread to receive MAVLink messages"""
        while self._running and self._connection:
            try:
                msg = self._connection.recv_match(blocking=True, timeout=1)
                if msg:
                    self._process_message(msg)
            except Exception as e:
                if self._running:
                    logger.error(f"Receive error: {e}")

    def _process_message(self, msg):
        """Process incoming MAVLink message"""
        msg_type = msg.get_type()

        with self._lock:
            if msg_type == "HEARTBEAT":
                self._telemetry.last_heartbeat = time.time()
                self._telemetry.mode = self.COPTER_MODES.get(msg.custom_mode, "UNKNOWN")
                self._telemetry.armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                self._telemetry.system_status = msg.system_status

            elif msg_type == "SYS_STATUS":
                self._telemetry.battery_voltage = msg.voltage_battery / 1000.0
                self._telemetry.battery_current = msg.current_battery / 100.0
                self._telemetry.battery_remaining = msg.battery_remaining

            elif msg_type == "GPS_RAW_INT":
                self._telemetry.latitude = msg.lat / 1e7
                self._telemetry.longitude = msg.lon / 1e7
                self._telemetry.altitude_msl = msg.alt / 1000.0
                self._telemetry.satellites = msg.satellites_visible
                self._telemetry.fix_type = msg.fix_type
                self._telemetry.hdop = msg.eph / 100.0 if msg.eph != 65535 else 0

            elif msg_type == "GLOBAL_POSITION_INT":
                self._telemetry.latitude = msg.lat / 1e7
                self._telemetry.longitude = msg.lon / 1e7
                self._telemetry.altitude = msg.relative_alt / 1000.0
                self._telemetry.altitude_msl = msg.alt / 1000.0

            elif msg_type == "ATTITUDE":
                import math
                self._telemetry.roll = math.degrees(msg.roll)
                self._telemetry.pitch = math.degrees(msg.pitch)
                self._telemetry.yaw = math.degrees(msg.yaw)

            elif msg_type == "VFR_HUD":
                self._telemetry.ground_speed = msg.groundspeed
                self._telemetry.air_speed = msg.airspeed
                self._telemetry.climb_rate = msg.climb

            elif msg_type == "HOME_POSITION":
                self._telemetry.home_lat = msg.latitude / 1e7
                self._telemetry.home_lon = msg.longitude / 1e7
                self._telemetry.home_alt = msg.altitude / 1000.0

            self._telemetry.last_update = time.time()

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(self._telemetry)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def register_callback(self, callback: Callable[[TelemetryData], None]):
        """Register telemetry callback"""
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[TelemetryData], None]):
        """Unregister telemetry callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    # ========================
    # COMMAND METHODS
    # ========================

    def arm(self) -> CommandResult:
        """Arm the vehicle"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.command_long_send(
                self._connection.target_system,
                self._connection.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # confirmation
                1,  # arm
                0, 0, 0, 0, 0, 0
            )

            # Wait for ACK
            ack = self._connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return CommandResult(True, "Armed successfully")
            else:
                return CommandResult(False, f"Arm failed: {ack.result if ack else 'No ACK'}")

        except Exception as e:
            return CommandResult(False, f"Arm error: {e}")

    def disarm(self) -> CommandResult:
        """Disarm the vehicle"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.command_long_send(
                self._connection.target_system,
                self._connection.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,
                0,  # disarm
                0, 0, 0, 0, 0, 0
            )

            ack = self._connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return CommandResult(True, "Disarmed successfully")
            else:
                return CommandResult(False, f"Disarm failed: {ack.result if ack else 'No ACK'}")

        except Exception as e:
            return CommandResult(False, f"Disarm error: {e}")

    def takeoff(self, altitude: float) -> CommandResult:
        """Takeoff to specified altitude"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.command_long_send(
                self._connection.target_system,
                self._connection.target_component,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0,
                0, 0, 0, 0, 0, 0,
                altitude
            )

            ack = self._connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return CommandResult(True, f"Takeoff to {altitude}m initiated")
            else:
                return CommandResult(False, f"Takeoff failed: {ack.result if ack else 'No ACK'}")

        except Exception as e:
            return CommandResult(False, f"Takeoff error: {e}")

    def land(self) -> CommandResult:
        """Land the vehicle"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.command_long_send(
                self._connection.target_system,
                self._connection.target_component,
                mavutil.mavlink.MAV_CMD_NAV_LAND,
                0,
                0, 0, 0, 0, 0, 0, 0
            )

            ack = self._connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return CommandResult(True, "Land initiated")
            else:
                return CommandResult(False, f"Land failed: {ack.result if ack else 'No ACK'}")

        except Exception as e:
            return CommandResult(False, f"Land error: {e}")

    def rtl(self) -> CommandResult:
        """Return to launch"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.command_long_send(
                self._connection.target_system,
                self._connection.target_component,
                mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                0,
                0, 0, 0, 0, 0, 0, 0
            )

            ack = self._connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return CommandResult(True, "RTL initiated")
            else:
                return CommandResult(False, f"RTL failed: {ack.result if ack else 'No ACK'}")

        except Exception as e:
            return CommandResult(False, f"RTL error: {e}")

    def set_mode(self, mode_name: str) -> CommandResult:
        """Set flight mode"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        mode_name = mode_name.upper()
        if mode_name not in self.COPTER_MODE_NUMBERS:
            return CommandResult(False, f"Unknown mode: {mode_name}")

        mode_id = self.COPTER_MODE_NUMBERS[mode_name]

        try:
            self._connection.mav.command_long_send(
                self._connection.target_system,
                self._connection.target_component,
                mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                0,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id,
                0, 0, 0, 0, 0
            )

            ack = self._connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
            if ack and ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return CommandResult(True, f"Mode changed to {mode_name}")
            else:
                return CommandResult(False, f"Mode change failed: {ack.result if ack else 'No ACK'}")

        except Exception as e:
            return CommandResult(False, f"Mode change error: {e}")

    def goto(self, lat: float, lon: float, alt: float) -> CommandResult:
        """Go to position (requires GUIDED mode)"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.mission_item_int_send(
                self._connection.target_system,
                self._connection.target_component,
                0,  # seq
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                2,  # current (2 = guided mode destination)
                1,  # autocontinue
                0, 0, 0, 0,  # params
                int(lat * 1e7),
                int(lon * 1e7),
                alt
            )
            return CommandResult(True, f"Going to ({lat}, {lon}, {alt}m)")

        except Exception as e:
            return CommandResult(False, f"Goto error: {e}")

    def get_parameter(self, param_name: str) -> CommandResult:
        """Get parameter value"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.param_request_read_send(
                self._connection.target_system,
                self._connection.target_component,
                param_name.encode('utf-8'),
                -1
            )

            msg = self._connection.recv_match(type='PARAM_VALUE', blocking=True, timeout=5)
            if msg:
                return CommandResult(True, f"{param_name} = {msg.param_value}",
                                    {"name": param_name, "value": msg.param_value})
            else:
                return CommandResult(False, f"Parameter {param_name} not found")

        except Exception as e:
            return CommandResult(False, f"Get parameter error: {e}")

    def set_parameter(self, param_name: str, value: float) -> CommandResult:
        """Set parameter value"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.param_set_send(
                self._connection.target_system,
                self._connection.target_component,
                param_name.encode('utf-8'),
                value,
                mavutil.mavlink.MAV_PARAM_TYPE_REAL32
            )

            msg = self._connection.recv_match(type='PARAM_VALUE', blocking=True, timeout=5)
            if msg and msg.param_value == value:
                return CommandResult(True, f"Set {param_name} = {value}")
            else:
                return CommandResult(False, f"Failed to set {param_name}")

        except Exception as e:
            return CommandResult(False, f"Set parameter error: {e}")

    def reboot(self) -> CommandResult:
        """Reboot flight controller"""
        if not self.connected:
            return CommandResult(False, "Not connected")

        try:
            self._connection.mav.command_long_send(
                self._connection.target_system,
                self._connection.target_component,
                mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
                0,
                1,  # Reboot autopilot
                0, 0, 0, 0, 0, 0
            )
            return CommandResult(True, "Reboot command sent")

        except Exception as e:
            return CommandResult(False, f"Reboot error: {e}")

    def execute_command(self, command: Dict[str, Any]) -> CommandResult:
        """Execute command from AI backend"""
        cmd_type = command.get("type", "").upper()
        params = command.get("params", {})

        logger.info(f"Executing: {cmd_type} with params: {params}")

        if cmd_type == "ARM":
            return self.arm()
        elif cmd_type == "DISARM":
            return self.disarm()
        elif cmd_type == "TAKEOFF":
            return self.takeoff(params.get("altitude", 10))
        elif cmd_type == "LAND":
            return self.land()
        elif cmd_type == "RTL":
            return self.rtl()
        elif cmd_type == "CHANGE_MODE":
            return self.set_mode(params.get("mode", "LOITER"))
        elif cmd_type == "GOTO":
            return self.goto(
                params.get("latitude"),
                params.get("longitude"),
                params.get("altitude", 20)
            )
        elif cmd_type == "GET_PARAM":
            return self.get_parameter(params.get("name", ""))
        elif cmd_type == "SET_PARAM":
            return self.set_parameter(params.get("name", ""), params.get("value", 0))
        elif cmd_type == "REBOOT":
            return self.reboot()
        else:
            return CommandResult(False, f"Unknown command: {cmd_type}")


# Singleton instance for global access
_manager_instance: Optional[MAVLinkManager] = None

def get_mavlink_manager() -> MAVLinkManager:
    """Get singleton MAVLink manager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MAVLinkManager()
    return _manager_instance
