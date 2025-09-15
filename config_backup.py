"""Configuration settings for the Smart Energy Monitor"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "energy_monitor.db"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Data collection settings
POLLING_INTERVAL = 60  # seconds between readings
BATCH_SIZE = 100       # readings to process at once

# AI model settings
AI_ENABLED = True  # Set to False to disable AI features entirely
USE_MOCK_AI = True  # Set to False when gpt-oss is available
MODEL_NAME = "gpt-oss-20b"  # Will be updated when model is available
FALLBACK_MODEL = "microsoft/DialoGPT-medium"  # Fallback model for testing
MAX_CONTEXT_LENGTH = 2048
TEMPERATURE = 0.7
MAX_RESPONSE_TOKENS = 200

# AI analysis settings
ANALYSIS_LOOKBACK_DAYS = 7  # Days of data to analyze
MIN_DATA_POINTS = 10  # Minimum readings needed for analysis
INSIGHT_CACHE_HOURS = 6  # Cache insights for this many hours

# Device configuration - Realistic home energy monitoring setup
ENERGY_SENSORS = {
    # Living room entertainment
    "living_room_tv": {
        "type": "ct_sensor",
        "adc_channel": 0,
        "ct_ratio": 2000,
        "voltage": 120,
        "name": "Living Room TV",
        "calibration_factor": 1.0,
        "location": "Living Room"
    },
    
    # Kitchen appliances
    "kitchen_microwave": {
        "type": "ct_sensor",
        "adc_channel": 1,
        "ct_ratio": 2000,
        "voltage": 120,
        "name": "Kitchen Microwave", 
        "calibration_factor": 1.0,
        "location": "Kitchen"
    },
    "kitchen_fridge": {
        "type": "ct_sensor",
        "adc_channel": 2,
        "ct_ratio": 2000,
        "voltage": 120,
        "name": "Kitchen Fridge",
        "calibration_factor": 1.0,
        "location": "Kitchen"
    },
    
    # HVAC system
    "bedroom_ac": {
        "type": "ct_sensor",
        "adc_channel": 3,
        "ct_ratio": 2000,
        "voltage": 120,
        "name": "Bedroom AC",
        "calibration_factor": 1.0,
        "location": "Bedroom"
    },
    
    # Home office
    "office_computer": {
        "type": "ct_sensor",
        "adc_channel": 4,
        "ct_ratio": 2000,
        "voltage": 120,
        "name": "Home Office Computer",
        "calibration_factor": 1.0,
        "location": "Office"
    },
    
    # Laundry room
    "laundry_washer": {
        "type": "ct_sensor",
        "adc_channel": 5,
        "ct_ratio": 2000,
        "voltage": 120,
        "name": "Washing Machine",
        "calibration_factor": 1.0,
        "location": "Laundry Room"
    },
    "laundry_dryer": {
        "type": "ct_sensor",
        "adc_channel": 6,
        "ct_ratio": 2000,
        "voltage": 240,  # 240V for electric dryer
        "name": "Electric Dryer",
        "calibration_factor": 1.0,
        "location": "Laundry Room"
    }
}

# ADC Configuration (MCP3008)
ADC_SPI_PORT = 0
ADC_SPI_DEVICE = 0
ADC_VREF = 3.3  # Reference voltage

# Web interface settings
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
DEBUG_MODE = True

# Energy cost settings (update for your location)
ELECTRICITY_RATE = float(os.getenv('ELECTRICITY_RATE', '0.12'))  # dollars per kWh
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '$')

# Environment-based overrides
if os.getenv('SMART_ENERGY_DEBUG'):
    DEBUG_MODE = True
    POLLING_INTERVAL = 30  # Faster polling in debug mode

if os.getenv('SMART_ENERGY_AI_DISABLED'):
    AI_ENABLED = False

# Hardware detection
RASPBERRY_PI_DETECTED = os.path.exists('/proc/device-tree/model')
if RASPBERRY_PI_DETECTED:
    try:
        with open('/proc/device-tree/model', 'r') as f:
            PI_MODEL = f.read().strip()
    except:
        PI_MODEL = "Unknown Raspberry Pi"
else:
    PI_MODEL = None$')$')$')$')$')$')

# Environment-based overrides
if os.getenv('SMART_ENERGY_DEBUG'):
    DEBUG_MODE = True
    POLLING_INTERVAL = 30  # Faster polling in debug mode

if os.getenv('SMART_ENERGY_AI_DISABLED'):
    AI_ENABLED = False

# Hardware detection
RASPBERRY_PI_DETECTED = os.path.exists('/proc/device-tree/model')
if RASPBERRY_PI_DETECTED:
    try:
        with open('/proc/device-tree/model', 'r') as f:
            PI_MODEL = f.read().strip()
    except:
        PI_MODEL = "Unknown Raspberry Pi"
else:
    PI_MODEL = None