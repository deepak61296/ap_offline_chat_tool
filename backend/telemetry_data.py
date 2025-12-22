"""
Telemetry data structures for Mission Planner integration
Provides read-only access to drone telemetry data
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class BatteryInfo:
    """Battery telemetry data"""
    voltage: float = 0.0  # Volts
    current: float = 0.0  # Amps
    remaining: int = 0    # Percentage (0-100)
    consumed: float = 0.0 # mAh consumed


@dataclass
class GPSInfo:
    """GPS and position data"""
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0      # Meters (relative to home)
    altitude_msl: float = 0.0  # Meters (mean sea level)
    satellites: int = 0
    fix_type: str = "NO_FIX"   # NO_FIX, 2D, 3D, DGPS, RTK
    hdop: float = 0.0          # Horizontal dilution of precision


@dataclass
class AttitudeInfo:
    """Attitude and orientation data"""
    roll: float = 0.0    # Degrees
    pitch: float = 0.0   # Degrees
    yaw: float = 0.0     # Degrees (heading)
    roll_rate: float = 0.0
    pitch_rate: float = 0.0
    yaw_rate: float = 0.0


@dataclass
class SpeedInfo:
    """Speed and velocity data"""
    ground_speed: float = 0.0  # m/s
    air_speed: float = 0.0     # m/s
    climb_rate: float = 0.0    # m/s (vertical speed)


@dataclass
class FlightStatus:
    """Flight status and mode information"""
    mode: str = "UNKNOWN"
    armed: bool = False
    system_status: str = "STANDBY"  # STANDBY, ACTIVE, CRITICAL, etc.
    ekf_ok: bool = False
    gps_ok: bool = False


@dataclass
class MissionInfo:
    """Mission and waypoint information"""
    current_waypoint: int = 0
    total_waypoints: int = 0
    distance_to_waypoint: float = 0.0  # Meters
    bearing_to_waypoint: float = 0.0   # Degrees


@dataclass
class HomeInfo:
    """Home position information"""
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    distance_from_home: float = 0.0  # Meters
    bearing_from_home: float = 0.0   # Degrees


@dataclass
class SensorInfo:
    """Sensor data"""
    vibration_x: float = 0.0
    vibration_y: float = 0.0
    vibration_z: float = 0.0
    rangefinder: float = 0.0  # Meters (distance to ground)
    temperature: float = 0.0  # Celsius


@dataclass
class TelemetryData:
    """Complete telemetry data package"""
    battery: Optional[BatteryInfo] = None
    gps: Optional[GPSInfo] = None
    attitude: Optional[AttitudeInfo] = None
    speed: Optional[SpeedInfo] = None
    status: Optional[FlightStatus] = None
    mission: Optional[MissionInfo] = None
    home: Optional[HomeInfo] = None
    sensors: Optional[SensorInfo] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {}
        
        if self.battery:
            result["battery"] = {
                "voltage": self.battery.voltage,
                "current": self.battery.current,
                "remaining": self.battery.remaining,
                "consumed": self.battery.consumed
            }
        
        if self.gps:
            result["gps"] = {
                "latitude": self.gps.latitude,
                "longitude": self.gps.longitude,
                "altitude": self.gps.altitude,
                "altitude_msl": self.gps.altitude_msl,
                "satellites": self.gps.satellites,
                "fix_type": self.gps.fix_type,
                "hdop": self.gps.hdop
            }
        
        if self.attitude:
            result["attitude"] = {
                "roll": self.attitude.roll,
                "pitch": self.attitude.pitch,
                "yaw": self.attitude.yaw,
                "roll_rate": self.attitude.roll_rate,
                "pitch_rate": self.attitude.pitch_rate,
                "yaw_rate": self.attitude.yaw_rate
            }
        
        if self.speed:
            result["speed"] = {
                "ground_speed": self.speed.ground_speed,
                "air_speed": self.speed.air_speed,
                "climb_rate": self.speed.climb_rate
            }
        
        if self.status:
            result["status"] = {
                "mode": self.status.mode,
                "armed": self.status.armed,
                "system_status": self.status.system_status,
                "ekf_ok": self.status.ekf_ok,
                "gps_ok": self.status.gps_ok
            }
        
        if self.mission:
            result["mission"] = {
                "current_waypoint": self.mission.current_waypoint,
                "total_waypoints": self.mission.total_waypoints,
                "distance_to_waypoint": self.mission.distance_to_waypoint,
                "bearing_to_waypoint": self.mission.bearing_to_waypoint
            }
        
        if self.home:
            result["home"] = {
                "latitude": self.home.latitude,
                "longitude": self.home.longitude,
                "altitude": self.home.altitude,
                "distance_from_home": self.home.distance_from_home,
                "bearing_from_home": self.home.bearing_from_home
            }
        
        if self.sensors:
            result["sensors"] = {
                "vibration_x": self.sensors.vibration_x,
                "vibration_y": self.sensors.vibration_y,
                "vibration_z": self.sensors.vibration_z,
                "rangefinder": self.sensors.rangefinder,
                "temperature": self.sensors.temperature
            }
        
        return result


def format_telemetry_for_prompt(telemetry: Dict[str, Any]) -> str:
    """
    Format telemetry data into a human-readable string for AI context
    """
    lines = []
    
    if "battery" in telemetry:
        b = telemetry["battery"]
        lines.append(f"Battery: {b['voltage']:.1f}V, {b['current']:.1f}A, {b['remaining']}% remaining")
    
    if "gps" in telemetry:
        g = telemetry["gps"]
        lines.append(f"GPS: {g['satellites']} satellites, {g['fix_type']}, Alt: {g['altitude']:.1f}m")
    
    if "attitude" in telemetry:
        a = telemetry["attitude"]
        lines.append(f"Attitude: Roll {a['roll']:.1f}, Pitch {a['pitch']:.1f}, Yaw {a['yaw']:.1f}")
    
    if "speed" in telemetry:
        s = telemetry["speed"]
        lines.append(f"Speed: Ground {s['ground_speed']:.1f} m/s, Climb {s['climb_rate']:.1f} m/s")
    
    if "status" in telemetry:
        st = telemetry["status"]
        armed_str = "ARMED" if st["armed"] else "DISARMED"
        lines.append(f"Status: {st['mode']}, {armed_str}")
    
    if "mission" in telemetry:
        m = telemetry["mission"]
        lines.append(f"Mission: WP {m['current_waypoint']}/{m['total_waypoints']}, {m['distance_to_waypoint']:.0f}m away")
    
    if "home" in telemetry:
        h = telemetry["home"]
        lines.append(f"Home: {h['distance_from_home']:.0f}m away, bearing {h['bearing_from_home']:.0f}")
    
    return "\n".join(lines) if lines else "No telemetry data available"