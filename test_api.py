#!/usr/bin/env python3
"""Test API endpoints"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_interface import app
import json

def test_api():
    """Test API endpoints"""
    with app.test_client() as client:
        print("Testing API endpoints...")
        
        # Test devices endpoint
        print("\n1. Testing /api/devices")
        response = client.get('/api/devices')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Devices: {len(data)} found")
            for device in data:
                print(f"  - {device['name']} ({device['id']})")
        else:
            print(f"Error: {response.get_data(as_text=True)}")
        
        # Test energy summary endpoint
        print("\n2. Testing /api/energy_summary")
        response = client.get('/api/energy_summary')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Summary: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.get_data(as_text=True)}")
        
        # Test current readings endpoint
        print("\n3. Testing /api/current_readings")
        response = client.get('/api/current_readings')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Readings: {len(data)} found")
            for reading in data[:3]:  # Show first 3
                print(f"  - {reading['device_id']}: {reading['power_watts']}W")
        else:
            print(f"Error: {response.get_data(as_text=True)}")

if __name__ == '__main__':
    test_api()