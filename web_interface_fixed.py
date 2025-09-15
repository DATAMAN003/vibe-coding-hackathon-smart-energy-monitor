#!/usr/bin/env python3
"""
Smart Energy Monitor - Fixed Web Interface
Flask web application with comprehensive API endpoints
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import os
from datetime import datetime, timedelta
from ai_analyzer import EnergyAIAnalyzer
from energy_calculator import EnergyCalculator
import config

app = Flask(__name__)

def get_db_connection():
    """Get database connection - prioritize fresh database"""
    # Priority order for database selection
    db_candidates = [
        str(config.DATABASE_PATH),  # Current config path
        'fresh_energy_monitor.db',  # Synchronized fresh database
        'realistic_energy_monitor.db',  # Fresh realistic database
        'energy_monitor.db'  # Fallback old database
    ]
    
    db_path = None
    for candidate in db_candidates:
        if os.path.exists(candidate):
            db_path = candidate
            break
    
    # If no database exists, use the config path (will be created)
    if db_path is None:
        db_path = str(config.DATABASE_PATH)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_time_warp_status():
    """Check if we're in time warp mode based on data span"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest
            FROM energy_readings
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result and result['earliest'] and result['latest']:
            earliest = datetime.fromisoformat(result['earliest'])
            latest = datetime.fromisoformat(result['latest'])
            span_days = (latest - earliest).days
            return span_days > 100  # Time warp if more than 100 days of data
        return False
    except Exception as e:
        print(f"Error checking time warp status: {e}")
        return False

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/insights')
def insights():
    """AI insights page"""
    return render_template('insights.html')

@app.route('/device/<device_id>')
def device_detail(device_id):
    """Device detail page"""
    return render_template('device_detail.html', device_id=device_id)

# API Endpoints
@app.route('/api/current_readings')
def api_current_readings():
    """Get current energy readings for all devices"""
    try:
        calculator = EnergyCalculator()
        daily_data = calculator.calculate_daily_energy_from_power_reading()
        
        readings = []
        for device in daily_data['devices']:
            readings.append({
                'device_id': device['device_id'],
                'device_name': device['device_name'],
                'power_watts': device['avg_power_watts'],
                'voltage': 120.0,  # Default voltage
                'current_amps': device['avg_power_watts'] / 120.0,  # Calculate current
                'energy_kwh': device['avg_power_watts'] / 1000.0,  # Estimate energy
                'timestamp': datetime.now().isoformat(),
                'status': device['status'].lower(),  # Convert to lowercase for consistency
                'cost_per_hour': round(device['avg_power_watts'] * config.ELECTRICITY_RATE / 1000, 4)
            })
        
        return jsonify(readings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/device_history/<device_id>')
def api_device_history(device_id):
    """Get historical data for a specific device"""
    try:
        hours = request.args.get('hours', 24, type=int)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Convert device_id back to device_name
        device_name = device_id.replace('_', ' ').title()
        cursor.execute("""
            SELECT timestamp, power_watts
            FROM energy_readings 
            WHERE device_name LIKE ? 
            AND datetime(timestamp) >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
            LIMIT 1000
        """.format(hours), (f'%{device_name}%',))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'timestamp': row['timestamp'],
                'power_watts': row['power_watts'],
                'voltage': 120.0,
                'current_amps': row['power_watts'] / 120.0,
                'energy_kwh': row['power_watts'] / 1000.0
            })
        
        conn.close()
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/total_consumption')
def api_total_consumption():
    """Get total energy consumption and cost"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current total power
        cursor.execute("""
            SELECT SUM(power_watts) as total_power
            FROM energy_readings 
            WHERE timestamp IN (
                SELECT MAX(timestamp) 
                FROM energy_readings 
                GROUP BY device_id
            )
        """)
        result = cursor.fetchone()
        total_power = result['total_power'] or 0
        
        # Get daily energy consumption
        cursor.execute("""
            SELECT SUM(power_watts) / 1000.0 * COUNT(*) * ? / 3600.0 as daily_kwh
            FROM energy_readings 
            WHERE date(timestamp) = date('now')
        """, (config.POLLING_INTERVAL,))
        result = cursor.fetchone()
        daily_kwh = result['daily_kwh'] or 0
        
        # Calculate costs
        daily_cost = daily_kwh * config.ELECTRICITY_RATE
        monthly_cost = daily_cost * 30
        
        conn.close()
        return jsonify({
            'total_power_watts': round(total_power, 2),
            'daily_kwh': round(daily_kwh, 3),
            'daily_cost': round(daily_cost, 2),
            'monthly_cost': round(monthly_cost, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/home_analysis')
def api_home_analysis():
    """Get comprehensive home energy analysis"""
    try:
        analyzer = EnergyAIAnalyzer()
        analysis = analyzer.analyze_home_energy()
        return jsonify(analysis)
    except Exception as e:
        print(f"Home analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/device_analysis/<device_id>')
def api_device_analysis(device_id):
    """Get AI analysis for specific device"""
    try:
        analyzer = EnergyAIAnalyzer()
        analysis = analyzer.analyze_device_patterns(device_id)
        return jsonify(analysis)
    except Exception as e:
        print(f"Device analysis error for {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily_report')
def api_daily_report():
    """Get daily energy report"""
    try:
        calculator = EnergyCalculator()
        daily_data = calculator.calculate_daily_energy_from_actual_data()
        
        # Get time warp status
        is_time_warp = get_time_warp_status()
        
        # Calculate top consumers for JavaScript compatibility
        top_consumers = {d['device_name']: d['total_cost'] for d in sorted(daily_data['devices'], key=lambda x: x['total_cost'], reverse=True)[:5]}
        
        report = {
            'date': daily_data['date'],
            'total_consumption_kwh': daily_data['total_energy_kwh'],
            'total_cost': daily_data['total_cost'],
            'devices': daily_data['devices'],
            'is_time_warp': is_time_warp,
            'summary': {
                'date': daily_data['date'],
                'total_energy_kwh': daily_data['total_energy_kwh'],
                'total_cost': daily_data['total_cost'],
                'peak_power_watts': daily_data['peak_power_watts']
            },
            'top_energy_consumers': top_consumers,
            'insights': [
                f"📊 Total consumption for {daily_data['date']}: {daily_data['total_energy_kwh']:.2f} kWh",
                f"💰 Daily cost: ${daily_data['total_cost']:.2f}",
                f"⚡ Peak device power: {daily_data['peak_power_watts']:.0f}W"
            ],
            'recommendations': [
                "🔌 Monitor high-power devices during peak hours",
                "💡 Consider energy-efficient alternatives for top consumers",
                "📈 Track daily patterns to optimize usage"
            ]
        }
        
        return jsonify(report)
    except Exception as e:
        print(f"Daily report error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monthly_analysis')
def api_monthly_analysis():
    """Get monthly energy analysis"""
    try:
        calculator = EnergyCalculator()
        now = datetime.now()
        monthly_data = calculator.calculate_monthly_analysis(now.year, now.month)
        
        # Get time warp status
        is_time_warp = get_time_warp_status()
        
        # Calculate top consumers for JavaScript compatibility
        top_consumers = {d['device_name']: d['total_cost'] for d in sorted(monthly_data['devices'], key=lambda x: x['total_cost'], reverse=True)[:5]}
        
        current_month_name = now.strftime('%B')
        current_year = now.year
        
        analysis = {
            'months': [monthly_data],
            'is_time_warp': is_time_warp,
            'summary': f"Analyzed {monthly_data['total_devices']} devices for {monthly_data['month']}",
            'current_month': {
                'name': current_month_name,
                'year': current_year,
                'data': {
                    'top_consumers': top_consumers
                }
            },
            'projections': {
                'projected_kwh': monthly_data['projected_kwh'],
                'projected_cost': f"${monthly_data['projected_cost']:.2f}",
                'current_kwh': monthly_data['total_energy_kwh'],
                'days_elapsed': monthly_data['days_elapsed'],
                'peak_power': f"{monthly_data['peak_power_watts']:.0f}",
                'active_devices': monthly_data['active_devices']
            },
            'comparison': {
                'last_month_name': None,
                'last_month_cost': None,
                'change_percent': 0,
                'change_direction': 'stable'
            },
            'historical_months': [monthly_data],
            'insights': [
                f"📊 Current month usage: {monthly_data['total_energy_kwh']:.2f} kWh",
                f"💰 Projected monthly cost: ${monthly_data['projected_cost']:.2f}",
                f"📈 Daily average: {monthly_data['total_energy_kwh'] / max(1, monthly_data['days_elapsed']):.2f} kWh" if monthly_data['days_elapsed'] > 0 else "📊 Start collecting data for insights"
            ],
            'predictions': [
                f"🔮 Based on current usage, expect ~{monthly_data['projected_kwh']:.0f} kWh this month",
                "📅 Peak usage typically occurs during evening hours"
            ],
            'recommendations': [
                "💡 Monitor your highest consuming devices",
                "🌙 Shift non-essential usage to off-peak hours",
                "🔌 Unplug devices when not in use"
            ]
        }
        
        return jsonify(analysis)
    except Exception as e:
        print(f"Monthly analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/time_warp_status')
def api_time_warp_status():
    """Get time warp mode status"""
    try:
        is_time_warp = get_time_warp_status()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total_readings FROM energy_readings")
        total_readings = cursor.fetchone()['total_readings']
        
        cursor.execute("""
            SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest
            FROM energy_readings
        """)
        result = cursor.fetchone()
        
        span_info = "No data"
        if result and result['earliest'] and result['latest']:
            earliest = datetime.fromisoformat(result['earliest'])
            latest = datetime.fromisoformat(result['latest'])
            span_days = (latest - earliest).days
            span_info = f"{span_days} days of data"
        
        conn.close()
        
        return jsonify({
            'is_time_warp': is_time_warp,
            'total_readings': total_readings,
            'data_span': span_info,
            'mode': 'Time Warp Demo' if is_time_warp else 'Real-time Monitoring'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/energy_summary')
def api_energy_summary():
    """Get energy summary for dashboard"""
    try:
        calculator = EnergyCalculator()
        summary = calculator.get_current_power_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices')
def api_devices():
    """Get list of all devices"""
    try:
        # Get device list from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT device_name FROM energy_readings ORDER BY device_name")
        
        devices = []
        for row in cursor.fetchall():
            device_name = row['device_name']
            device_id = device_name.lower().replace(' ', '_').replace('-', '_')
            # Guess location from device name
            location = 'Unknown'
            if 'living' in device_name.lower():
                location = 'Living Room'
            elif 'kitchen' in device_name.lower():
                location = 'Kitchen'
            elif 'bedroom' in device_name.lower():
                location = 'Bedroom'
            elif 'office' in device_name.lower():
                location = 'Office'
            elif 'laundry' in device_name.lower() or 'washing' in device_name.lower() or 'dryer' in device_name.lower():
                location = 'Laundry'
            
            devices.append({
                'id': device_id,
                'name': device_name,
                'location': location
            })
        
        conn.close()
        return jsonify(devices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical_data/<device_id>')
def api_historical_data(device_id):
    """Get historical data for chart display"""
    try:
        hours = request.args.get('hours', 24, type=int)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Convert device_id back to device_name for query
        device_name = device_id.replace('_', ' ').title()
        cursor.execute("""
            SELECT timestamp, power_watts
            FROM energy_readings 
            WHERE device_name LIKE ? 
            AND datetime(timestamp) >= datetime('now', '-{} hours')
            ORDER BY timestamp ASC
            LIMIT 100
        """.format(hours), (f'%{device_name}%',))
        
        data = cursor.fetchall()
        
        timestamps = [row['timestamp'] for row in data]
        power_watts = [row['power_watts'] for row in data]
        
        conn.close()
        return jsonify({
            'timestamps': timestamps,
            'power_watts': power_watts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)