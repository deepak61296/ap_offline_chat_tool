"""ArduPilot AI Backend - Core Module

A modular AI backend for ArduPilot ground control stations.
Provides HTTP API for AI-powered drone assistance with RAG-enhanced responses.

Version: 2.1.0
"""

__version__ = "2.1.0"
__author__ = "Deepak"
__description__ = "AI Backend for ArduPilot Mission Planner with RAG support"

# Core modules
from .api_server import app
from .config import DEFAULT_MODEL, API_HOST, API_PORT
from .rag import get_rag, ArduPilotRAG

__all__ = [
    'app',
    'DEFAULT_MODEL',
    'API_HOST',
    'API_PORT',
    'get_rag',
    'ArduPilotRAG'
]
