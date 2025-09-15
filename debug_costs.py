#!/usr/bin/env python3
"""
Debug cost discrepancy between dashboard and AI insights
"""

import requests
import json

def debug_costs():
    print("🔍 DEBUGGING COST DISCREPANCY")
    print("=" * 50)
    
    try:
        # Test dashboard API
        print("📊 Testing Dashboard API...")
        response = requests.get('http://localhost:5000/api/energy_summary')
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: ✅ Success")
            print(f"   Daily cost: ${data.get('daily_cost', 'N/A')}")
            print(f"   Monthly estimate: ${data.get('monthly_estimate', 'N/A')}")
            print(f"   Total power: {data.get('total_power_watts', 'N/A')}W")
            print(f"   Raw response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Status: ❌ Failed ({response.status_code})")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    try:
        # Test AI insights API
        print("🤖 Testing AI Insights API...")
        response = requests.get('http://localhost:5000/api/daily_report')
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: ✅ Success")
            print(f"   Total cost: ${data.get('total_cost', 'N/A')}")
            print(f"   Total energy: {data.get('total_consumption_kwh', 'N/A')} kWh")
            print(f"   Raw response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Status: ❌ Failed ({response.status_code})")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    try:
        # Test monthly analysis API
        print("📅 Testing Monthly Analysis API...")
        response = requests.get('http://localhost:5000/api/monthly_analysis')
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: ✅ Success")
            print(f"   Monthly cost: ${data.get('total_monthly_cost', 'N/A')}")
            print(f"   Daily average: ${data.get('avg_daily_cost', 'N/A')}")
            print(f"   Raw response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Status: ❌ Failed ({response.status_code})")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    debug_costs()