#!/usr/bin/env python3
"""
Check what's actually in the database
"""

import sqlite3
from datetime import datetime

def check_database():
    """Check database contents"""
    print("🔍 DATABASE ANALYSIS")
    print("=" * 30)
    
    conn = sqlite3.connect("energy_monitor.db")
    cursor = conn.cursor()
    
    # Check devices table
    cursor.execute("SELECT COUNT(*) FROM devices")
    devices_count = cursor.fetchone()[0]
    print(f"📊 Devices table: {devices_count} devices")
    
    cursor.execute("SELECT device_id, device_name FROM devices")
    devices = cursor.fetchall()
    print("   Device list:")
    for device_id, device_name in devices:
        print(f"     {device_id} -> {device_name}")
    
    # Check readings table
    cursor.execute("SELECT COUNT(*) FROM energy_readings")
    readings_count = cursor.fetchone()[0]
    print(f"\n📈 Readings table: {readings_count} total readings")
    
    cursor.execute("SELECT COUNT(DISTINCT device_name) FROM energy_readings")
    unique_devices = cursor.fetchone()[0]
    print(f"📱 Unique devices in readings: {unique_devices}")
    
    cursor.execute("SELECT DISTINCT device_name FROM energy_readings")
    reading_devices = cursor.fetchall()
    print("   Devices with readings:")
    for device in reading_devices:
        print(f"     {device[0]}")
    
    # Check latest readings (what dashboard shows)
    print(f"\n⚡ LATEST READINGS (Dashboard data):")
    cursor.execute("""
        SELECT device_name, power_watts, timestamp
        FROM energy_readings 
        WHERE timestamp IN (
            SELECT MAX(timestamp) 
            FROM energy_readings 
            GROUP BY device_name
        )
        ORDER BY device_name
    """)
    
    latest_readings = cursor.fetchall()
    total_current_power = 0
    for device_name, power, timestamp in latest_readings:
        total_current_power += power
        print(f"     {device_name}: {power:.1f}W at {timestamp}")
    
    print(f"\n💡 CURRENT TOTALS:")
    print(f"   Total Power: {total_current_power:.1f}W")
    print(f"   Devices Count: {len(latest_readings)}")
    
    # Check today's data for daily report
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT device_name, 
               AVG(power_watts) as avg_power,
               MAX(power_watts) as peak_power,
               COUNT(*) as readings_count
        FROM energy_readings 
        WHERE date(timestamp) = ?
        GROUP BY device_name
    """, (today,))
    
    today_data = cursor.fetchall()
    print(f"\n📅 TODAY'S DATA ({today}):")
    total_avg_power = 0
    for device_name, avg_power, peak_power, count in today_data:
        total_avg_power += avg_power
        print(f"     {device_name}: Avg {avg_power:.1f}W, Peak {peak_power:.1f}W, {count} readings")
    
    print(f"\n📊 DAILY CALCULATIONS:")
    print(f"   Average total power today: {total_avg_power:.1f}W")
    
    # Calculate daily energy (this is what daily report shows)
    daily_kwh = 0
    for device_name, avg_power, peak_power, count in today_data:
        # Energy = average power * time
        hours_of_data = count * 60 / 3600  # Assuming 60 second intervals
        device_kwh = avg_power * hours_of_data / 1000
        daily_kwh += device_kwh
        print(f"     {device_name}: {device_kwh:.4f} kWh")
    
    daily_cost = daily_kwh * 0.12
    print(f"   Total daily energy: {daily_kwh:.4f} kWh")
    print(f"   Total daily cost: ${daily_cost:.4f}")
    
    conn.close()

if __name__ == "__main__":
    check_database()