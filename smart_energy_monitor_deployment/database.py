"""Database operations for energy monitoring data"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import config

class EnergyDatabase:
    def __init__(self, db_path: Path = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS energy_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    power_watts REAL NOT NULL,
                    voltage REAL,
                    current REAL,
                    energy_kwh REAL,
                    cost REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    device_name TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    location TEXT,
                    ip_address TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    insight_type TEXT NOT NULL,
                    insight_text TEXT NOT NULL,
                    confidence_score REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_device_time ON energy_readings(device_id, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_device ON ai_insights(device_id)")
            
            conn.commit()
    
    def add_reading(self, device_id: str, device_name: str, power_watts: float, 
                   voltage: float = None, current: float = None, energy_kwh: float = None):
        """Add a new energy reading"""
        timestamp = datetime.now()
        cost = (energy_kwh or 0) * config.ELECTRICITY_RATE
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO energy_readings 
                (device_id, device_name, timestamp, power_watts, voltage, current, energy_kwh, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (device_id, device_name, timestamp, power_watts, voltage, current, energy_kwh, cost))
            conn.commit()
    
    def get_recent_readings(self, device_id: str = None, hours: int = 24) -> List[Dict]:
        """Get recent readings for analysis"""
        since = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if device_id:
                cursor = conn.execute("""
                    SELECT * FROM energy_readings 
                    WHERE device_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (device_id, since))
            else:
                cursor = conn.execute("""
                    SELECT * FROM energy_readings 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (since,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_device_stats(self, device_id: str, days: int = 7) -> Dict:
        """Get statistical summary for a device"""
        since = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as reading_count,
                    AVG(power_watts) as avg_power,
                    MAX(power_watts) as max_power,
                    MIN(power_watts) as min_power,
                    SUM(energy_kwh) as total_energy,
                    SUM(cost) as total_cost
                FROM energy_readings 
                WHERE device_id = ? AND timestamp >= ?
            """, (device_id, since))
            
            row = cursor.fetchone()
            return {
                'reading_count': row[0] or 0,
                'avg_power': row[1] or 0,
                'max_power': row[2] or 0,
                'min_power': row[3] or 0,
                'total_energy': row[4] or 0,
                'total_cost': row[5] or 0
            }
    
    def add_device(self, device_id: str, device_name: str, device_type: str, 
                   location: str = None, ip_address: str = None):
        """Register a new device"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO devices 
                (device_id, device_name, device_type, location, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (device_id, device_name, device_type, location, ip_address))
            conn.commit()
    
    def save_ai_insight(self, device_id: str, insight_type: str, insight_text: str, confidence: float = 0.8):
        """Save an AI-generated insight"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ai_insights (device_id, insight_type, insight_text, confidence_score)
                VALUES (?, ?, ?, ?)
            """, (device_id, insight_type, insight_text, confidence))
            conn.commit()