"""Configuration for the ArduPilot AI backend server."""

import argparse
import os
import platform

# Detect platform
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# Parse command-line arguments
parser = argparse.ArgumentParser(description='ArduPilot AI Backend Server')
parser.add_argument('--no-gpu', action='store_true',
                    help='Disable GPU usage (CPU-only mode)')
parser.add_argument('--low-power', action='store_true',
                    help='Low-power mode for less powerful CPUs (reduces context size)')
parser.add_argument('--standalone', action='store_true',
                    help='Enable standalone mode with direct MAVLink connection')
parser.add_argument('--connect', type=str, default='',
                    help='MAVLink connection string (e.g., tcp:127.0.0.1:5760, /dev/ttyUSB0, COM3)')
parser.add_argument('--baud', type=int, default=57600,
                    help='Baud rate for serial connections (default: 57600)')
args, unknown = parser.parse_known_args()

# API Server Configuration
API_HOST = '0.0.0.0'
API_PORT = 5000
API_DEBUG = False

# Model Configuration
DEFAULT_MODEL = 'qwen2.5:3b'
SUPPORTED_MODELS = ['qwen2.5:3b']

# CPU/GPU Configuration
USE_GPU = not args.no_gpu
LOW_POWER_MODE = args.low_power

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_NUM_CTX = 2048 if LOW_POWER_MODE else 4096  # Context window size
OLLAMA_NUM_GPU = 0 if not USE_GPU else -1  # 0 = CPU only, -1 = auto

# Safety Limits
MAX_PARAM_VALUE = 1000000  # Maximum parameter value
MIN_PARAM_VALUE = -1000000  # Minimum parameter value
MOVEMENT_MAX_DISTANCE = 1000  # Maximum movement distance in meters
TAKEOFF_MAX_ALTITUDE = 500  # Maximum takeoff altitude in meters
GOTO_MAX_DISTANCE = 10000  # Maximum GOTO distance in meters

# Command Timeouts
COMMAND_TIMEOUT = 30  # seconds
PARAM_FETCH_TIMEOUT = 10  # seconds

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Supported Flight Modes
SUPPORTED_MODES = [
    'STABILIZE', 'ACRO', 'ALT_HOLD', 'AUTO', 'GUIDED',
    'LOITER', 'RTL', 'CIRCLE', 'LAND', 'DRIFT',
    'SPORT', 'FLIP', 'AUTOTUNE', 'POSHOLD', 'BRAKE',
    'THROW', 'AVOID_ADSB', 'GUIDED_NOGPS', 'SMART_RTL',
    'FLOWHOLD', 'FOLLOW', 'ZIGZAG', 'SYSTEMID', 'AUTOROTATE',
    'AUTO_RTL'
]

# Parameter Categories (for filtering)
PARAM_CATEGORIES = {
    'ARMING': ['ARMING_', 'ARM_'],
    'BATTERY': ['BATT_', 'BATT1_', 'BATT2_'],
    'GPS': ['GPS_', 'GPS1_', 'GPS2_'],
    'COMPASS': ['COMPASS_', 'COMP_'],
    'RC': ['RC_', 'RC1_', 'RC2_'],
    'SERVO': ['SERVO_', 'SERVO1_'],
    'FENCE': ['FENCE_'],
    'WPNAV': ['WPNAV_'],
    'PILOT': ['PILOT_'],
    'ANGLE': ['ANGLE_'],
    'RATE': ['RATE_']
}

# Standalone mode config

# Enable standalone mode (direct MAVLink connection)
STANDALONE_MODE = args.standalone

# MAVLink connection settings
MAVLINK_CONNECTION = args.connect or os.getenv("MAVLINK_CONNECTION", "")
MAVLINK_BAUD = args.baud

# Default connection strings for different platforms
DEFAULT_CONNECTIONS = {
    "sitl": "tcp:127.0.0.1:5760",
    "sitl_udp": "udp:127.0.0.1:14550",
    "serial_linux": "/dev/ttyUSB0",
    "serial_linux_acm": "/dev/ttyACM0",
    "serial_windows": "COM3",
}

# Telemetry streaming rate (Hz)
TELEMETRY_RATE = 1  # 1 Hz for arming status updates

# Command approval config

# Approval modes: "manual", "smart", "autonomous"
# manual: Ask for every command
# smart: Auto-approve LOW risk, ask for MEDIUM/HIGH
# autonomous: Auto-approve all (dangerous!)
APPROVAL_MODE = os.getenv("APPROVAL_MODE", "smart")

# Command risk levels
COMMAND_RISK_LEVELS = {
    "GET_PARAM": "low",
    "ARM": "medium",
    "DISARM": "medium",
    "CHANGE_MODE": "medium",
    "SET_PARAM": "medium",
    "TAKEOFF": "high",
    "LAND": "high",
    "RTL": "high",
    "GOTO": "high",
    "GOTO_HOME": "high",
    "MOVE_DIRECTION": "high",
    "ALTITUDE_CHANGE": "high",
    "SET_SPEED": "medium",
    "SET_YAW": "medium",
    "REBOOT": "critical",
}

# GCS integration config

# Operation modes
# "integrated": GCS sends telemetry, backend returns commands for GCS to execute
# "standalone": Backend connects directly via MAVLink
OPERATION_MODE = "standalone" if STANDALONE_MODE else "integrated"

# Backend version
BACKEND_VERSION = "3.0.0"
