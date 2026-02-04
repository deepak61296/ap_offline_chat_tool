"""
ArduPilot AI Backend Package
Multi-GCS Support: Mission Planner, MAVProxy, QGroundControl, Standalone

Cross-platform: Windows and Linux compatible
"""

__version__ = '2.4.0'

# Core modules
from .api_server import app
from .commands import extract_command, validate_command
from .prompts import get_agent_prompt, get_ask_prompt, get_script_prompt
from .config import (
    DEFAULT_MODEL,
    SCRIPT_MODEL,
    API_HOST,
    API_PORT,
    SUPPORTED_MODES,
    STANDALONE_MODE,
    OPERATION_MODE,
    BACKEND_VERSION
)

# MAVLink manager (optional)
try:
    from .mavlink_manager import MAVLinkManager, get_mavlink_manager, PYMAVLINK_AVAILABLE
except ImportError:
    MAVLinkManager = None
    get_mavlink_manager = None
    PYMAVLINK_AVAILABLE = False

__all__ = [
    # API
    'app',

    # Commands
    'extract_command',
    'validate_command',

    # Prompts
    'get_agent_prompt',
    'get_ask_prompt',
    'get_script_prompt',

    # Config
    'DEFAULT_MODEL',
    'SCRIPT_MODEL',
    'API_HOST',
    'API_PORT',
    'SUPPORTED_MODES',
    'STANDALONE_MODE',
    'OPERATION_MODE',
    'BACKEND_VERSION',

    # MAVLink (optional)
    'MAVLinkManager',
    'get_mavlink_manager',
    'PYMAVLINK_AVAILABLE'
]
