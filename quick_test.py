#!/usr/bin/env python3
import requests
import time

print("🔍 QUICK COST TEST")
print("=" * 30)

time.sleep(3)  # Wait for data

try:
    # Dashboard API
    r1 = requests.get('http://localhost:5000/api/energy_summary')
    dashboard = r1.json()
    print(f"📊 Dashboard: ${dashboard.get('daily_cost', 'N/A')}")
    
    # AI Insights API  
    r2 = requests.get('http://localhost:5000/api/daily_report')
    insights = r2.json()
    print(f"🤖 AI Insights: ${insights.get('total_cost', 'N/A')}")
    
    # Monthly API
    r3 = requests.get('http://localhost:5000/api/monthly_analysis')
    monthly = r3.json()
    print(f"📅 Monthly: ${monthly.get('projections', {}).get('projected_cost', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error: {e}")