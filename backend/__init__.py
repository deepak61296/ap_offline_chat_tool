"""
ArduPilot AI Backend Package
Provides AI-powered chat assistance for ArduPilot Mission Planner
"""

__version__ = '2.1.0'

# Core modules
from .api_server import app
from .commands import extract_command, validate_command
from .prompts import get_agent_prompt, get_ask_prompt
from .config import (
    DEFAULT_MODEL,
    API_HOST,
    API_PORT,
    SUPPORTED_MODES
)

__all__ = [
    'app',
    'extract_command',
    'validate_command', 
    'get_agent_prompt',
    'get_ask_prompt',
    'DEFAULT_MODEL',
    'API_HOST',
    'API_PORT',
    'SUPPORTED_MODES'
]
