#!/usr/bin/env python3
"""Test daily report endpoint"""

try:
    from web_interface_fixed import app
    
    with app.test_client() as client:
        response = client.get('/api/daily_report')
        print(f"Daily report status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Total cost: {data.get('total_cost')}")
            print(f"Devices count: {len(data.get('devices', []))}")
        else:
            print(f"Error: {response.data}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()