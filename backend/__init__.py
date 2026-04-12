"""ArduPilot AI Backend — Agentic Pipeline v3."""

__version__ = '3.0.0'

# Core pipeline
from .api_server import app
from .planner import plan
from .executor import execute

# Tool definitions
from .tools import TOOL_DEFINITIONS, extract_tool_calls, normalize_tool_call

# Legacy (backward compat)
from .commands import extract_command, validate_command

# Configuration
from .config import (
    DEFAULT_MODEL,
    API_HOST, API_PORT,
    SUPPORTED_MODES, STANDALONE_MODE,
    OPERATION_MODE, BACKEND_VERSION
)

# MAVLink manager (optional)
try:
    from .mavlink_manager import MAVLinkManager, get_mavlink_manager, PYMAVLINK_AVAILABLE
except ImportError:
    MAVLinkManager = None
    get_mavlink_manager = None
    PYMAVLINK_AVAILABLE = False

__all__ = [
    'app', 'plan', 'execute',
    'TOOL_DEFINITIONS', 'extract_tool_calls', 'normalize_tool_call',
    'extract_command', 'validate_command',
    'DEFAULT_MODEL', 'API_HOST', 'API_PORT',
    'SUPPORTED_MODES', 'STANDALONE_MODE', 'OPERATION_MODE', 'BACKEND_VERSION',
    'MAVLinkManager', 'get_mavlink_manager', 'PYMAVLINK_AVAILABLE',
]
