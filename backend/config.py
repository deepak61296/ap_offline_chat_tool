"""
Configuration settings for ArduPilot AI Backend
Centralized configuration for API server, models, and safety limits
"""

import argparse
import os

# Parse command-line arguments
parser = argparse.ArgumentParser(description='ArduPilot AI Backend Server')
parser.add_argument('--no-gpu', action='store_true', 
                    help='Disable GPU usage (CPU-only mode)')
parser.add_argument('--low-power', action='store_true',
                    help='Low-power mode for less powerful CPUs (reduces context size)')
args, unknown = parser.parse_known_args()

# API Server Configuration
API_HOST = '0.0.0.0'
API_PORT = 5000
API_DEBUG = False

# Model Configuration
DEFAULT_MODEL = 'qwen2.5:3b'

# CPU/GPU Configuration
USE_GPU = not args.no_gpu
LOW_POWER_MODE = args.low_power

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_NUM_CTX = 2048 if LOW_POWER_MODE else 4096  # Context window size
OLLAMA_NUM_GPU = 0 if not USE_GPU else -1  # 0 = CPU only, -1 = auto

# RAG Configuration  
RAG_MAX_CONTEXT = 800 if LOW_POWER_MODE else 1500  # Max chars from docs
RAG_NUM_RESULTS = 2 if LOW_POWER_MODE else 3  # Number of doc chunks

AVAILABLE_MODELS = [
    # Qwen models (recommended for ArduPilot)
    'qwen2.5:3b',
    'qwen2.5:7b',
    'qwen2.5:14b',
    
    # Gemma models (Google)
    'gemma2:2b',
    'gemma2:9b',
    
    # Llama models (Meta)
    'llama3.2:3b',
    'llama3.1:8b',
    
    # Mistral models
    'mistral:7b',
    
    # Phi models (Microsoft)
    'phi3:3.8b',
    'phi3:14b'
]

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
