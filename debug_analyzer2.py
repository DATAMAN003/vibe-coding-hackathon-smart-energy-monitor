#!/usr/bin/env python3
"""
Debug the AI analyzer step by step
"""

from ai_analyzer import EnergyAIAnalyzer
import pandas as pd

def debug_step_by_step():
    print("🔍 Step-by-step debugging...")
    
    analyzer = EnergyAIAnalyzer()
    device_id = 'laundry_dryer'
    days = 7
    
    print(f"1. Getting readings for {device_id}...")
    readings = analyzer.db.get_recent_readings(device_id, hours=days*24)
    print(f"   Found {len(readings)} readings")
    
    if not readings:
        print("   No readings - would return early structure")
        return
    
    print("2. Converting to DataFrame...")
    df = pd.DataFrame(readings)
    print(f"   DataFrame shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    
    print("3. Processing timestamps...")
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'] >= 5
        print("   ✅ Timestamp processing successful")
    except Exception as e:
        print(f"   ❌ Timestamp processing failed: {e}")
        df['hour'] = 12
        df['day_of_week'] = 1
        df['is_weekend'] = False
    
    print("4. Calculating statistics...")
    try:
        stats = analyzer._calculate_device_stats(df)
        print(f"   ✅ Statistics calculated: {list(stats.keys())}")
    except Exception as e:
        print(f"   ❌ Statistics calculation failed: {e}")
        return
    
    print("5. Generating insights...")
    try:
        insights = analyzer._generate_device_insights(device_id, df, stats)
        print(f"   ✅ Generated {len(insights)} insights")
    except Exception as e:
        print(f"   ❌ Insights generation failed: {e}")
        return
    
    print("6. Converting numpy types...")
    try:
        stats_json = {}
        for key, value in stats.items():
            if hasattr(value, 'item'):  # numpy scalar
                stats_json[key] = value.item()
            else:
                stats_json[key] = value
        print("   ✅ Numpy conversion successful")
    except Exception as e:
        print(f"   ❌ Numpy conversion failed: {e}")
        return
    
    print("7. Generating recommendations...")
    try:
        recommendations = analyzer._generate_recommendations(device_id, df, stats)
        print(f"   ✅ Generated {len(recommendations)} recommendations")
    except Exception as e:
        print(f"   ❌ Recommendations generation failed: {e}")
        return
    
    print("8. Building final result...")
    try:
        result = {
            'device_id': device_id,
            'analysis_period_days': days,
            'statistics': stats_json,
            'insights': insights,
            'recommendations': recommendations
        }
        print(f"   ✅ Final result keys: {list(result.keys())}")
        return result
    except Exception as e:
        print(f"   ❌ Final result building failed: {e}")
        return

if __name__ == "__main__":
    result = debug_step_by_step()
    if result:
        print(f"\n✅ SUCCESS: All steps completed, device_id = {result.get('device_id', 'MISSING')}")
    else:
        print("\n❌ FAILED: Debug stopped at some step")