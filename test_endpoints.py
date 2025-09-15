#!/usr/bin/env python3
"""Test API endpoints"""

import requests
import json

base_url = "http://localhost:5000"

endpoints = [
    "/api/energy_summary",
    "/api/devices", 
    "/api/current_readings",
    "/api/daily_report",
    "/api/monthly_analysis",
    "/api/time_warp_status"
]

for endpoint in endpoints:
    try:
        print(f"\nTesting {endpoint}...")
        response = requests.get(f"{base_url}{endpoint}", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"Exception: {e}")