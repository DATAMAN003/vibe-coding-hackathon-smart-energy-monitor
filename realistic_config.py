"""
Realistic Configuration for Smart Energy Monitor
Optimized for 99.9% accurate real-world simulation
"""

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

# Realistic data collection settings
POLLING_INTERVAL = 30  # 30 seconds for more responsive real-time updates
BATCH_SIZE = 50       # Smaller batches for real-time feel

# Realistic energy cost settings (US average 2024)
ELECTRICITY_RATE = 0.1168  # $0.1168 per kWh (US national average)
CURRENCY_SYMBOL = '$'

# Time-of-Use rates (if applicable)
TOU_RATES = {
    'peak': 0.1568,      # 4 PM - 9 PM weekdays
    'off_peak': 0.0968,  # 10 PM - 6 AM daily
    'mid_peak': 0.1168   # All other times
}

# Peak hours definition
PEAK_HOURS = {
    'weekday': [(16, 21)],  # 4 PM - 9 PM
    'weekend': [(18, 22)]   # 6 PM - 10 PM
}

# Seasonal electricity rate adjustments
SEASONAL_RATE_MULTIPLIERS = {
    'winter': 1.15,  # Higher rates in winter (heating season)
    'summer': 1.25,  # Highest rates in summer (AC season)
    'spring': 0.95,  # Lower rates in mild weather
    'fall': 1.00     # Base rate
}

# Realistic device power consumption ranges (watts)
REALISTIC_DEVICE_SPECS = {
    'Living Room TV': {
        'standby': (1, 3),
        'active': (80, 150),
        'high': (150, 200),
        'annual_kwh': 150,  # Typical annual consumption
        'energy_star_rating': 4.2
    },
    'Kitchen Microwave': {
        'standby': (1, 2),
        'active': (1000, 1200),
        'high': (1200, 1500),
        'annual_kwh': 60,
        'energy_star_rating': 4.0
    },
    'Kitchen Fridge': {
        'standby': (35, 45),
        'active': (120, 180),
        'high': (180, 220),
        'annual_kwh': 400,
        'energy_star_rating': 4.5
    },
    'Bedroom AC': {
        'standby': (3, 8),
        'active': (1500, 2200),
        'high': (2200, 3000),
        'annual_kwh': 1200,
        'energy_star_rating': 3.8
    },
    'Home Office Computer': {
        'standby': (5, 12),
        'active': (200, 300),
        'high': (300, 400),
        'annual_kwh': 200,
        'energy_star_rating': 4.1
    },
    'Washing Machine': {
        'standby': (1, 3),
        'active': (400, 600),
        'high': (600, 900),
        'annual_kwh': 90,
        'energy_star_rating': 4.3
    },
    'Electric Dryer': {
        'standby': (2, 5),
        'active': (2000, 2800),
        'high': (2800, 3500),
        'annual_kwh': 769,
        'energy_star_rating': 3.9
    }
}

# Realistic usage patterns (probability of being active by hour)
HOURLY_USAGE_PATTERNS = {
    'Living Room TV': {
        0: 0.05, 1: 0.02, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.02,
        6: 0.15, 7: 0.25, 8: 0.20, 9: 0.10, 10: 0.08, 11: 0.12,
        12: 0.15, 13: 0.18, 14: 0.20, 15: 0.25, 16: 0.35, 17: 0.50,
        18: 0.70, 19: 0.85, 20: 0.90, 21: 0.80, 22: 0.60, 23: 0.25
    },
    'Kitchen Microwave': {
        0: 0.01, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00, 5: 0.02,
        6: 0.15, 7: 0.30, 8: 0.25, 9: 0.10, 10: 0.05, 11: 0.20,
        12: 0.40, 13: 0.30, 14: 0.15, 15: 0.10, 16: 0.15, 17: 0.25,
        18: 0.45, 19: 0.35, 20: 0.20, 21: 0.10, 22: 0.05, 23: 0.02
    },
    'Kitchen Fridge': {  # Always on, but compressor cycles
        0: 0.60, 1: 0.55, 2: 0.50, 3: 0.50, 4: 0.50, 5: 0.55,
        6: 0.65, 7: 0.70, 8: 0.75, 9: 0.80, 10: 0.85, 11: 0.90,
        12: 0.95, 13: 0.90, 14: 0.85, 15: 0.80, 16: 0.85, 17: 0.90,
        18: 0.95, 19: 0.90, 20: 0.85, 21: 0.80, 22: 0.75, 23: 0.65
    },
    'Bedroom AC': {  # Seasonal and temperature dependent
        0: 0.70, 1: 0.75, 2: 0.80, 3: 0.80, 4: 0.75, 5: 0.70,
        6: 0.60, 7: 0.40, 8: 0.30, 9: 0.25, 10: 0.30, 11: 0.40,
        12: 0.60, 13: 0.80, 14: 0.90, 15: 0.95, 16: 0.90, 17: 0.80,
        18: 0.70, 19: 0.60, 20: 0.55, 21: 0.60, 22: 0.65, 23: 0.70
    },
    'Home Office Computer': {  # Work hours focused
        0: 0.05, 1: 0.02, 2: 0.01, 3: 0.01, 4: 0.02, 5: 0.05,
        6: 0.10, 7: 0.20, 8: 0.60, 9: 0.85, 10: 0.90, 11: 0.85,
        12: 0.70, 13: 0.85, 14: 0.90, 15: 0.85, 16: 0.80, 17: 0.70,
        18: 0.50, 19: 0.30, 20: 0.20, 21: 0.15, 22: 0.10, 23: 0.05
    },
    'Washing Machine': {  # Daytime usage, higher on weekends
        0: 0.01, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00, 5: 0.01,
        6: 0.02, 7: 0.05, 8: 0.10, 9: 0.20, 10: 0.25, 11: 0.20,
        12: 0.15, 13: 0.20, 14: 0.25, 15: 0.20, 16: 0.15, 17: 0.10,
        18: 0.08, 19: 0.05, 20: 0.03, 21: 0.02, 22: 0.01, 23: 0.01
    },
    'Electric Dryer': {  # Follows washing machine patterns
        0: 0.01, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00, 5: 0.01,
        6: 0.02, 7: 0.03, 8: 0.05, 9: 0.15, 10: 0.20, 11: 0.25,
        12: 0.20, 13: 0.25, 14: 0.30, 15: 0.25, 16: 0.20, 17: 0.15,
        18: 0.10, 19: 0.08, 20: 0.05, 21: 0.03, 22: 0.02, 23: 0.01
    }
}

# Weekend usage multipliers
WEEKEND_MULTIPLIERS = {
    'Living Room TV': 1.4,
    'Kitchen Microwave': 1.2,
    'Kitchen Fridge': 1.1,
    'Bedroom AC': 1.1,
    'Home Office Computer': 0.3,  # Much less on weekends
    'Washing Machine': 2.0,  # Much more on weekends
    'Electric Dryer': 2.0
}

# Web interface settings
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
DEBUG_MODE = False  # Production-like for realistic app

# AI settings
AI_ENABLED = True
USE_MOCK_AI = True
ANALYSIS_LOOKBACK_DAYS = 7
MIN_DATA_POINTS = 5  # Lower threshold for faster insights

# Real-time update settings
DASHBOARD_REFRESH_INTERVAL = 15  # seconds
CHART_UPDATE_INTERVAL = 30      # seconds
INSIGHTS_REFRESH_INTERVAL = 300  # 5 minutes