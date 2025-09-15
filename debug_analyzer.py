#!/usr/bin/env python3
"""
Debug the AI analyzer to find why device_id is missing
"""

from ai_analyzer import EnergyAIAnalyzer
import json

def debug_analyzer():
    print("🔍 Debugging AI Analyzer...")
    
    analyzer = EnergyAIAnalyzer()
    
    # Test with dryer
    print("\n=== Testing Electric Dryer ===")
    try:
        result = analyzer.analyze_device_patterns('laundry_dryer')
        print("✅ Analysis completed")
        print("Keys in result:", list(result.keys()))
        
        if 'device_id' in result:
            print(f"Device ID: {result['device_id']}")
        else:
            print("❌ Missing device_id!")
            
        if 'statistics' in result:
            print("Statistics keys:", list(result['statistics'].keys()))
            
        if 'insights' in result:
            print(f"Insights count: {len(result['insights'])}")
            for i, insight in enumerate(result['insights']):
                print(f"  {i+1}. {insight}")
                
        # Print full result for debugging
        print("\n=== FULL RESULT ===")
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_analyzer()