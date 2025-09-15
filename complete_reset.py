#!/usr/bin/env python3
"""
Complete Reset - Fix all database synchronization issues
"""

import os
import sqlite3
import subprocess
import time
from datetime import datetime

def complete_reset():
    """Complete reset of the energy monitor system"""
    
    print("🔄 COMPLETE SYSTEM RESET")
    print("=" * 40)
    
    # Stop all Python processes
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
        print("🛑 Stopped all Python processes")
        time.sleep(2)
    except:
        pass
    
    # Remove ALL database files
    db_files = [
        "energy_monitor.db",
        "realistic_energy_monitor.db",
        "fresh_energy_monitor.db",
        "today_energy_monitor.db",
        "data/energy_monitor.db"
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️  Removed: {db_file}")
    
    # Create ONE fresh database
    db_path = "energy_monitor.db"
    print(f"🆕 Creating single database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
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
    
    cursor.execute("""
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
    
    # Add exactly 7 devices
    devices = [
        ("living_room_tv", "Living Room TV", "Living Room"),
        ("kitchen_microwave", "Kitchen Microwave", "Kitchen"),
        ("kitchen_fridge", "Kitchen Fridge", "Kitchen"),
        ("bedroom_ac", "Bedroom AC", "Bedroom"),
        ("office_computer", "Home Office Computer", "Office"),
        ("laundry_washer", "Washing Machine", "Laundry Room"),
        ("laundry_dryer", "Electric Dryer", "Laundry Room")
    ]
    
    current_time = datetime.now()
    
    for device_id, device_name, location in devices:
        # Add device
        cursor.execute("""
            INSERT INTO devices 
            (device_id, device_name, device_type, location, ip_address)
            VALUES (?, ?, 'smart_plug', ?, '192.168.1.100')
        """, (device_id, device_name, location))
        
        # Add ONE initial reading with current timestamp
        power = get_initial_power(device_name)
        voltage = 120.0
        current_amps = power / voltage
        energy_kwh = (power / 1000.0) * (1/60)  # 1 minute worth
        cost = energy_kwh * 0.12
        
        cursor.execute("""
            INSERT INTO energy_readings 
            (device_id, device_name, timestamp, power_watts, voltage, current, energy_kwh, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (device_id, device_name, current_time.isoformat(), power, voltage, current_amps, energy_kwh, cost))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database created with {len(devices)} devices")
    print(f"📅 Timestamp: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verify the database
    verify_database(db_path)

def get_initial_power(device_name):
    """Get realistic initial power for device"""
    if "TV" in device_name:
        return 45.0  # Standby
    elif "Microwave" in device_name:
        return 2.0   # Standby
    elif "Fridge" in device_name:
        return 150.0 # Running
    elif "AC" in device_name:
        return 8.0   # Standby (not hot right now)
    elif "Computer" in device_name:
        return 250.0 # Active (work hours)
    elif "Washing" in device_name:
        return 3.0   # Standby
    elif "Dryer" in device_name:
        return 5.0   # Standby
    return 10.0

def verify_database(db_path):
    """Verify database contents"""
    print(f"\n🔍 VERIFYING DATABASE: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM devices")
    device_count = cursor.fetchone()[0]
    print(f"   📱 Devices: {device_count}")
    
    cursor.execute("SELECT COUNT(*) FROM energy_readings")
    reading_count = cursor.fetchone()[0]
    print(f"   📊 Readings: {reading_count}")
    
    cursor.execute("SELECT COUNT(DISTINCT device_name) FROM energy_readings")
    unique_devices = cursor.fetchone()[0]
    print(f"   🔌 Unique devices in readings: {unique_devices}")
    
    cursor.execute("SELECT SUM(power_watts) FROM energy_readings")
    total_power = cursor.fetchone()[0]
    print(f"   ⚡ Total power: {total_power:.1f}W")
    
    conn.close()
    
    if device_count == 7 and unique_devices == 7:
        print("   ✅ Database verification PASSED")
        return True
    else:
        print("   ❌ Database verification FAILED")
        return False

if __name__ == "__main__":
    complete_reset()
    
    print("\n🚀 SYSTEM RESET COMPLETE!")
    print("Now run: python simple_energy_app.py")
    print("Expected results:")
    print("  • Dashboard: 7 devices")
    print("  • AI Insights: 7 devices, today's date")
    print("  • All numbers synchronized")