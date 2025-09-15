#!/usr/bin/env python3
"""Test web interface directly"""

try:
    from web_interface_fixed import app
    print("Web interface imported successfully")
    
    # Test a simple route
    with app.test_client() as client:
        response = client.get('/api/energy_summary')
        print(f"Energy summary status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.get_json()}")
        else:
            print(f"Error: {response.data}")
            
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()