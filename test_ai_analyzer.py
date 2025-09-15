#!/usr/bin/env python3
"""
Test what the AI analyzer is actually reading
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_analyzer import EnergyAIAnalyzer

def test_ai_analyzer():
    """Test what data the AI analyzer sees"""
    print("🔍 TESTING AI ANALYZER DATA")
    print("=" * 40)
    
    try:
        analyzer = EnergyAIAnalyzer()
        
        # Test home energy analysis
        print("📊 Testing home energy analysis...")
        home_analysis = analyzer.analyze_home_energy(days=1)
        
        print(f"   Total Devices: {home_analysis.get('total_devices', 'ERROR')}")
        print(f"   Total Energy: {home_analysis.get('total_energy_kwh', 'ERROR')} kWh")
        print(f"   Total Cost: ${home_analysis.get('total_cost', 'ERROR')}")
        
        # Check device summary
        device_summary = home_analysis.get('device_summary', {})
        print(f"   Devices in summary: {len(device_summary)}")
        
        for device_name, data in device_summary.items():
            print(f"     {device_name}: {data.get('avg_power_watts', 0):.1f}W avg")
        
        print("\n🔍 Raw database check...")
        # Check what's in the database directly
        db = analyzer.db
        readings = db.get_recent_readings(hours=24)
        
        print(f"   Recent readings count: {len(readings) if readings else 0}")
        if readings:
            unique_devices = set(r['device_name'] for r in readings)
            print(f"   Unique devices in readings: {len(unique_devices)}")
            for device in unique_devices:
                print(f"     {device}")
        
    except Exception as e:
        print(f"❌ Error testing AI analyzer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_analyzer()