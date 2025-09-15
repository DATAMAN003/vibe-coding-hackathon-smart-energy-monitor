#!/usr/bin/env python3
"""Check database schema"""

import sqlite3

def check_schema():
    try:
        conn = sqlite3.connect('energy_monitor.db')
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(energy_readings)")
        columns = cursor.fetchall()
        
        print("energy_readings table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check if we have any data
        cursor.execute("SELECT COUNT(*) FROM energy_readings")
        count = cursor.fetchone()[0]
        print(f"\nTotal readings: {count}")
        
        if count > 0:
            # Show sample data
            cursor.execute("SELECT * FROM energy_readings LIMIT 3")
            rows = cursor.fetchall()
            print("\nSample data:")
            for row in rows:
                print(f"  {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()