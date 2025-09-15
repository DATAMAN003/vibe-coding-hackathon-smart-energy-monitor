#!/usr/bin/env python3
"""Test database queries"""

import sqlite3
from datetime import datetime

def test_db():
    try:
        conn = sqlite3.connect('energy_monitor.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) as count FROM energy_readings")
        result = cursor.fetchone()
        print(f"Total readings: {result['count']}")
        
        # Test current readings query
        cursor.execute("""
            SELECT device_id, power_watts, timestamp
            FROM energy_readings 
            WHERE timestamp IN (
                SELECT MAX(timestamp) 
                FROM energy_readings 
                GROUP BY device_id
            )
            ORDER BY device_id
        """)
        
        readings = cursor.fetchall()
        print(f"Current readings: {len(readings)}")
        for row in readings:
            print(f"  {row['device_id']}: {row['power_watts']}W at {row['timestamp']}")
        
        # Test daily report query
        cursor.execute("""
            SELECT device_id, 
                   AVG(power_watts) as avg_power,
                   COUNT(*) as readings_count
            FROM energy_readings 
            WHERE date(timestamp) = date('now')
            GROUP BY device_id
        """)
        
        daily_data = cursor.fetchall()
        print(f"Daily data: {len(daily_data)} devices")
        for row in daily_data:
            print(f"  {row['device_id']}: {row['avg_power']:.1f}W avg, {row['readings_count']} readings")
        
        conn.close()
        print("Database queries successful!")
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    test_db()