"""Web interface for Smart Energy Monitor"""

from flask import Flask, render_template, jsonify, request
import json
from datetime import datetime, timedelta
from ai_analyzer import EnergyAIAnalyzer
from database import EnergyDatabase
import config

app = Flask(__name__)
app.secret_key = 'energy_monitor_secret_key'

# Initialize components
analyzer = EnergyAIAnalyzer(use_mock_ai=True)
db = EnergyDatabase()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/devices')
def get_devices():
    """Get list of all configured devices"""
    devices = []
    for device_id, device_config in config.ENERGY_SENSORS.items():
        devices.append({
            'id': device_id,
            'name': device_config['name'],
            'location': device_config.get('location', 'Unknown'),
            'type': device_config['type']
        })
    return jsonify(devices)

@app.route('/api/current_readings')
def get_current_readings():
    """Get current power readings for all devices"""
    # Add cache-busting headers to ensure fresh data
    from flask import make_response
    
    readings = db.get_recent_readings(hours=1)
    
    # Get the most recent reading for each device
    current_readings = {}
    for reading in readings:
        device_id = reading['device_id']
        if device_id not in current_readings or reading['timestamp'] > current_readings[device_id]['timestamp']:
            current_readings[device_id] = reading
    
    response = make_response(jsonify(list(current_readings.values())))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/api/device_analysis/<device_id>')
def get_device_analysis(device_id):
    """Get AI analysis for a specific device"""
    try:
        days = request.args.get('days', 7, type=int)
        analysis = analyzer.analyze_device_patterns(device_id, days)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route('/api/home_analysis')
def get_home_analysis():
    """Get home-wide energy analysis"""
    try:
        days = request.args.get('days', 7, type=int)
        analysis = analyzer.analyze_home_energy(days)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": f"Home analysis failed: {str(e)}"}), 500

@app.route('/api/daily_report')
def get_daily_report():
    """Get daily energy report"""
    try:
        report = analyzer.generate_daily_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": f"Daily report failed: {str(e)}"}), 500

@app.route('/api/historical_data/<device_id>')
def get_historical_data(device_id):
    """Get historical data for charts"""
    hours = request.args.get('hours', 24, type=int)
    readings = db.get_recent_readings(device_id, hours)
    
    # Format for chart display
    chart_data = {
        'timestamps': [r['timestamp'] for r in readings],
        'power_watts': [r['power_watts'] for r in readings],
        'cost': [r['cost'] for r in readings]
    }
    
    return jsonify(chart_data)

@app.route('/api/energy_summary')
def get_energy_summary():
    """Get energy summary for dashboard cards"""
    readings = db.get_recent_readings(hours=24)
    
    if not readings:
        return jsonify({
            'total_devices': 0,
            'total_power_watts': 0,
            'daily_cost': 0,
            'monthly_estimate': 0
        })
    
    # Calculate summary statistics
    total_power = sum(r['power_watts'] for r in readings[-7:])  # Last 7 readings (one per device)
    daily_cost = sum(r['cost'] for r in readings)
    monthly_estimate = daily_cost * 30
    
    return jsonify({
        'total_devices': len(config.ENERGY_SENSORS),
        'total_power_watts': round(total_power, 2),
        'daily_cost': round(daily_cost, 2),
        'monthly_estimate': round(monthly_estimate, 2)
    })

@app.route('/device/<device_id>')
def device_detail(device_id):
    """Device detail page"""
    device_config = config.ENERGY_SENSORS.get(device_id)
    if not device_config:
        return "Device not found", 404
    
    return render_template('device_detail.html', device_id=device_id, device_config=device_config)

@app.route('/insights')
def insights_page():
    """AI insights page"""
    return render_template('insights.html')

if __name__ == '__main__':
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=config.DEBUG_MODE)