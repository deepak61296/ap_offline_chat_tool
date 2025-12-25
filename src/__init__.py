"""
ArduPilot AI Assistant - Source Package
Natural language drone control with FunctionGemma
"""

from .drone_functions import DroneController, DRONE_FUNCTIONS
from .function_gemma import FunctionGemmaInterface

__version__ = "1.0.0"
__all__ = ["DroneController", "DRONE_FUNCTIONS", "FunctionGemmaInterface"]
