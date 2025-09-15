#!/usr/bin/env python3
"""
Fix cost calculations in existing database records
"""

import sqlite3
import config

def fix_database_costs():
    """Update all existing records with correct cost calculations"""
    print("🔧 Fixing cost calculations in database...")
    
    conn = sqlite3.connect(str(config.DATABASE_PATH))
    cursor = conn.cursor()
    
    # Get all records with energy_kwh data
    cursor.execute("SELECT id, energy_kwh FROM energy_readings WHERE energy_kwh IS NOT NULL")
    records = cursor.fetchall()
    
    print(f"📊 Found {len(records)} records to update")
    print(f"💰 Using electricity rate: ${config.ELECTRICITY_RATE}/kWh")
    
    updated_count = 0
    for record_id, energy_kwh in records:
        if energy_kwh is not None:
            correct_cost = energy_kwh * config.ELECTRICITY_RATE
            cursor.execute("UPDATE energy_readings SET cost = ? WHERE id = ?", (correct_cost, record_id))
            updated_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {updated_count} records with correct costs")
    
    # Verify the fix
    print("\n🔍 Verifying fix...")
    conn = sqlite3.connect(str(config.DATABASE_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT device_name, power_watts, energy_kwh, cost 
        FROM energy_readings 
        WHERE cost > 0 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    
    sample_records = cursor.fetchall()
    print("📋 Sample updated records:")
    for record in sample_records:
        device_name, power_watts, energy_kwh, cost = record
        print(f"  {device_name}: {power_watts:.1f}W, {energy_kwh:.6f} kWh, ${cost:.4f}")
    
    conn.close()
    print("✅ Cost fix completed!")

if __name__ == "__main__":
    fix_database_costs()