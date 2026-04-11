"""Configuration and runtime settings for the ArduPilot AI backend server."""

import argparse
import os
import platform
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# Detect platform
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# API Server Configuration
API_HOST = "0.0.0.0"
API_PORT = 5000
API_DEBUG = False

# Model Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen2.5:3b")
SCRIPT_MODEL = os.getenv("SCRIPT_MODEL", "qwen2.5-coder:7b")
SUPPORTED_MODELS = [DEFAULT_MODEL, SCRIPT_MODEL]

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Safety Limits
MAX_PARAM_VALUE = 1000000
MIN_PARAM_VALUE = -1000000
MOVEMENT_MAX_DISTANCE = 1000
TAKEOFF_MAX_ALTITUDE = 500
GOTO_MAX_DISTANCE = 10000

# Command Timeouts
COMMAND_TIMEOUT = 30
PARAM_FETCH_TIMEOUT = 10

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Supported Flight Modes
SUPPORTED_MODES = [
    "STABILIZE", "ACRO", "ALT_HOLD", "AUTO", "GUIDED",
    "LOITER", "RTL", "CIRCLE", "LAND", "DRIFT",
    "SPORT", "FLIP", "AUTOTUNE", "POSHOLD", "BRAKE",
    "THROW", "AVOID_ADSB", "GUIDED_NOGPS", "SMART_RTL",
    "FLOWHOLD", "FOLLOW", "ZIGZAG", "SYSTEMID", "AUTOROTATE",
    "AUTO_RTL"
]

# Parameter Categories (for filtering)
PARAM_CATEGORIES = {
    "ARMING": ["ARMING_", "ARM_"],
    "BATTERY": ["BATT_", "BATT1_", "BATT2_"],
    "GPS": ["GPS_", "GPS1_", "GPS2_"],
    "COMPASS": ["COMPASS_", "COMP_"],
    "RC": ["RC_", "RC1_", "RC2_"],
    "SERVO": ["SERVO_", "SERVO1_"],
    "FENCE": ["FENCE_"],
    "WPNAV": ["WPNAV_"],
    "PILOT": ["PILOT_"],
    "ANGLE": ["ANGLE_"],
    "RATE": ["RATE_"],
}

# Default connection strings for different platforms
DEFAULT_CONNECTIONS = {
    "sitl": "tcp:127.0.0.1:5760",
    "sitl_udp": "udp:127.0.0.1:14550",
    "serial_linux": "/dev/ttyUSB0",
    "serial_linux_acm": "/dev/ttyACM0",
    "serial_windows": "COM3",
}

# Telemetry streaming rate (Hz)
TELEMETRY_RATE = 1

# Approval modes: manual, smart, autonomous
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
    "LUA_SCRIPT": "high",
    "REBOOT": "critical",
}

# Backend version
BACKEND_VERSION = "3.1.0"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _unique_models(models: List[str]) -> List[str]:
    result: List[str] = []
    for model in models:
        if model and model not in result:
            result.append(model)
    return result


@dataclass(frozen=True)
class RuntimeSettings:
    api_host: str = API_HOST
    api_port: int = API_PORT
    api_debug: bool = API_DEBUG
    use_gpu: bool = True
    low_power_mode: bool = False
    standalone_mode: bool = False
    mavlink_connection: str = ""
    mavlink_baud: int = 57600
    default_model: str = DEFAULT_MODEL
    script_model: str = SCRIPT_MODEL
    supported_models: List[str] = field(default_factory=lambda: SUPPORTED_MODELS.copy())
    approval_mode: str = APPROVAL_MODE
    ollama_host: str = OLLAMA_HOST
    log_level: str = LOG_LEVEL
    log_format: str = LOG_FORMAT

    @property
    def operation_mode(self) -> str:
        return "standalone" if self.standalone_mode else "integrated"

    @property
    def ollama_num_ctx(self) -> int:
        return 2048 if self.low_power_mode else 4096

    @property
    def ollama_num_gpu(self) -> int:
        return 0 if not self.use_gpu else -1

    def summary(self) -> Dict[str, Any]:
        data = asdict(self)
        data["operation_mode"] = self.operation_mode
        data["ollama_num_ctx"] = self.ollama_num_ctx
        data["ollama_num_gpu"] = self.ollama_num_gpu
        return data


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ArduPilot AI Backend Server")
    parser.add_argument("--host", type=str, default=None, help="HTTP bind host")
    parser.add_argument("--port", type=int, default=None, help="HTTP bind port")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU usage (CPU-only mode)")
    parser.add_argument("--low-power", action="store_true", help="Low-power mode for smaller context size")
    parser.add_argument("--standalone", action="store_true", help="Enable standalone mode with direct MAVLink connection")
    parser.add_argument("--integrated", action="store_true", help="Force integrated compatibility mode")
    parser.add_argument("--connect", type=str, default=None, help="MAVLink connection string")
    parser.add_argument("--baud", type=int, default=None, help="Baud rate for serial MAVLink connections")
    parser.add_argument("--model", type=str, default=None, help="Default agent/ask model")
    parser.add_argument("--script-model", type=str, default=None, help="Default script generation model")
    return parser


def parse_runtime_settings(argv: Optional[List[str]] = None) -> RuntimeSettings:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    env_standalone = _env_flag("STANDALONE_MODE", False)
    standalone_mode = args.standalone or env_standalone
    if args.integrated:
        standalone_mode = False

    use_gpu = not (args.no_gpu or _env_flag("NO_GPU", False))
    low_power_mode = args.low_power or _env_flag("LOW_POWER_MODE", False)

    default_model = args.model or os.getenv("DEFAULT_MODEL", DEFAULT_MODEL)
    script_model = args.script_model or os.getenv("SCRIPT_MODEL", SCRIPT_MODEL)
    supported_models = _unique_models([
        default_model,
        script_model,
        *[
            model.strip()
            for model in os.getenv("SUPPORTED_MODELS", "").split(",")
            if model.strip()
        ],
    ])

    return RuntimeSettings(
        api_host=args.host or os.getenv("API_HOST", API_HOST),
        api_port=args.port or int(os.getenv("API_PORT", API_PORT)),
        api_debug=args.debug or _env_flag("API_DEBUG", API_DEBUG),
        use_gpu=use_gpu,
        low_power_mode=low_power_mode,
        standalone_mode=standalone_mode,
        mavlink_connection=args.connect or os.getenv("MAVLINK_CONNECTION", ""),
        mavlink_baud=args.baud or int(os.getenv("MAVLINK_BAUD", 57600)),
        default_model=default_model,
        script_model=script_model,
        supported_models=supported_models,
        approval_mode=os.getenv("APPROVAL_MODE", APPROVAL_MODE),
        ollama_host=os.getenv("OLLAMA_HOST", OLLAMA_HOST),
        log_level=os.getenv("LOG_LEVEL", LOG_LEVEL),
        log_format=os.getenv("LOG_FORMAT", LOG_FORMAT),
    )


def get_default_runtime_settings() -> RuntimeSettings:
    return parse_runtime_settings([])


DEFAULT_RUNTIME_SETTINGS = get_default_runtime_settings()

# Backward-compatible module exports for code paths that still import constants.
USE_GPU = DEFAULT_RUNTIME_SETTINGS.use_gpu
LOW_POWER_MODE = DEFAULT_RUNTIME_SETTINGS.low_power_mode
STANDALONE_MODE = DEFAULT_RUNTIME_SETTINGS.standalone_mode
MAVLINK_CONNECTION = DEFAULT_RUNTIME_SETTINGS.mavlink_connection
MAVLINK_BAUD = DEFAULT_RUNTIME_SETTINGS.mavlink_baud
OPERATION_MODE = DEFAULT_RUNTIME_SETTINGS.operation_mode
OLLAMA_NUM_CTX = DEFAULT_RUNTIME_SETTINGS.ollama_num_ctx
OLLAMA_NUM_GPU = DEFAULT_RUNTIME_SETTINGS.ollama_num_gpu
