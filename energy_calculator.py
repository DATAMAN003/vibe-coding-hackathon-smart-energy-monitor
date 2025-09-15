"""
Unified Energy Calculation Module
Ensures consistent calculations across all parts of the application
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import config

class EnergyCalculator:
    """Unified energy calculation class to ensure consistency"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.electricity_rate = config.ELECTRICITY_RATE
        self.active_device_threshold = 50.0  # Watts - devices above this are considered "Active"
        self.standby_device_threshold = 1.0  # Watts - devices above this are considered "Standby"
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def calculate_daily_energy_from_actual_data(self, target_date: str = None) -> Dict:
        """
        Calculate daily energy consumption from actual readings for a specific date
        This is the most accurate method as it uses real data
        """
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get actual readings for the target date
        cursor.execute("""
            SELECT 
                device_name,
                power_watts,
                timestamp,
                energy_kwh,
                cost
            FROM energy_readings 
            WHERE date(timestamp) = ?
            ORDER BY device_name, timestamp
        """, (target_date,))
        
        readings = cursor.fetchall()
        
        if not readings:
            # If no data for target date, get the most recent day with data
            cursor.execute("""
                SELECT 
                    device_name,
                    power_watts,
                    timestamp,
                    energy_kwh,
                    cost
                FROM energy_readings 
                WHERE date(timestamp) = (SELECT MAX(date(timestamp)) FROM energy_readings)
                ORDER BY device_name, timestamp
            """)
            readings = cursor.fetchall()
            if readings:
                target_date = readings[0]['timestamp'][:10]  # Extract date from timestamp
        
        if not readings:
            conn.close()
            return {
                'date': target_date,
                'total_energy_kwh': 0.0,
                'total_cost': 0.0,
                'peak_power_watts': 0.0,
                'devices': [],
                'active_devices': 0,
                'total_devices': 0
            }
        
        # Process readings by device
        device_data = {}
        for reading in readings:
            device_name = reading['device_name']
            if device_name not in device_data:
                device_data[device_name] = {
                    'device_name': device_name,
                    'readings': [],
                    'total_energy_kwh': 0.0,
                    'total_cost': 0.0,
                    'avg_power_watts': 0.0,
                    'peak_power_watts': 0.0
                }
            
            device_data[device_name]['readings'].append(reading)
            device_data[device_name]['total_energy_kwh'] += reading['energy_kwh'] or 0.0
            device_data[device_name]['total_cost'] += reading['cost'] or 0.0
            device_data[device_name]['peak_power_watts'] = max(
                device_data[device_name]['peak_power_watts'], 
                reading['power_watts'] or 0.0
            )
        
        # Calculate averages and finalize device data
        devices = []
        total_energy_kwh = 0.0
        total_cost = 0.0
        peak_power_watts = 0.0
        active_devices = 0
        
        for device_name, data in device_data.items():
            if data['readings']:
                data['avg_power_watts'] = sum(r['power_watts'] or 0 for r in data['readings']) / len(data['readings'])
                
                device_info = {
                    'device_name': device_name,
                    'device_id': device_name.lower().replace(' ', '_').replace('-', '_'),
                    'total_energy_kwh': round(data['total_energy_kwh'], 3),
                    'total_cost': round(data['total_cost'], 2),
                    'avg_power_watts': round(data['avg_power_watts'], 2),
                    'peak_power_watts': round(data['peak_power_watts'], 2),
                    'readings_count': len(data['readings']),
                    'status': self._get_device_status(data['avg_power_watts'])
                }
                
                devices.append(device_info)
                total_energy_kwh += data['total_energy_kwh']
                total_cost += data['total_cost']
                peak_power_watts = max(peak_power_watts, data['peak_power_watts'])
                
                if data['avg_power_watts'] >= self.active_device_threshold:
                    active_devices += 1
        
        conn.close()
        
        return {
            'date': target_date,
            'total_energy_kwh': round(total_energy_kwh, 3),
            'total_cost': round(total_cost, 2),
            'peak_power_watts': round(peak_power_watts, 2),
            'devices': devices,
            'active_devices': active_devices,
            'total_devices': len(devices)
        }
    
    def calculate_daily_energy_from_power_reading(self, target_date: str = None) -> Dict:
        """
        Calculate daily energy consumption from current power readings
        This is used for real-time dashboard when we don't have full day data
        """
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get latest power readings for each device
        cursor.execute("""
            SELECT 
                device_name,
                power_watts,
                timestamp
            FROM energy_readings 
            WHERE timestamp IN (
                SELECT MAX(timestamp) 
                FROM energy_readings 
                GROUP BY device_name
            )
        """)
        
        readings = cursor.fetchall()
        
        if not readings:
            conn.close()
            return {
                'date': target_date,
                'total_energy_kwh': 0.0,
                'total_cost': 0.0,
                'peak_power_watts': 0.0,
                'devices': [],
                'active_devices': 0,
                'total_devices': 0
            }
        
        devices = []
        total_power_watts = 0.0
        peak_power_watts = 0.0
        active_devices = 0
        
        for reading in readings:
            power_watts = reading['power_watts'] or 0.0
            device_name = reading['device_name']
            
            # Calculate projected daily energy (24 hours at current power)
            daily_energy_kwh = (power_watts * 24) / 1000
            daily_cost = daily_energy_kwh * self.electricity_rate
            
            device_info = {
                'device_name': device_name,
                'device_id': device_name.lower().replace(' ', '_').replace('-', '_'),
                'total_energy_kwh': round(daily_energy_kwh, 3),
                'total_cost': round(daily_cost, 2),
                'avg_power_watts': round(power_watts, 2),
                'peak_power_watts': round(power_watts, 2),
                'readings_count': 1,
                'status': self._get_device_status(power_watts)
            }
            
            devices.append(device_info)
            total_power_watts += power_watts
            peak_power_watts = max(peak_power_watts, power_watts)
            
            if power_watts >= self.active_device_threshold:
                active_devices += 1
        
        total_energy_kwh = (total_power_watts * 24) / 1000
        total_cost = total_energy_kwh * self.electricity_rate
        
        conn.close()
        
        return {
            'date': target_date,
            'total_energy_kwh': round(total_energy_kwh, 3),
            'total_cost': round(total_cost, 2),
            'peak_power_watts': round(peak_power_watts, 2),
            'devices': devices,
            'active_devices': active_devices,
            'total_devices': len(devices),
            'is_projected': True  # Flag to indicate this is projected data
        }
    
    def calculate_monthly_analysis(self, year: int = None, month: int = None) -> Dict:
        """
        Calculate monthly analysis with proper days elapsed calculation
        """
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get all data for the month
        cursor.execute("""
            SELECT 
                device_name,
                power_watts,
                timestamp,
                energy_kwh,
                cost
            FROM energy_readings 
            WHERE strftime('%Y-%m', timestamp) = ?
            ORDER BY device_name, timestamp
        """, (f"{year:04d}-{month:02d}",))
        
        readings = cursor.fetchall()
        
        if not readings:
            conn.close()
            return {
                'month': f"{year:04d}-{month:02d}",
                'total_energy_kwh': 0.0,
                'total_cost': 0.0,
                'peak_power_watts': 0.0,
                'devices': [],
                'active_devices': 0,
                'total_devices': 0,
                'days_elapsed': 0,
                'projected_kwh': 0.0,
                'projected_cost': 0.0
            }
        
        # Calculate actual days elapsed from data
        first_date = min(r['timestamp'][:10] for r in readings)
        last_date = max(r['timestamp'][:10] for r in readings)
        
        first_date_obj = datetime.strptime(first_date, '%Y-%m-%d')
        last_date_obj = datetime.strptime(last_date, '%Y-%m-%d')
        days_elapsed = (last_date_obj - first_date_obj).days + 1
        
        # Process readings by device
        device_data = {}
        for reading in readings:
            device_name = reading['device_name']
            if device_name not in device_data:
                device_data[device_name] = {
                    'device_name': device_name,
                    'total_energy_kwh': 0.0,
                    'total_cost': 0.0,
                    'power_readings': [],
                    'peak_power_watts': 0.0
                }
            
            device_data[device_name]['total_energy_kwh'] += reading['energy_kwh'] or 0.0
            device_data[device_name]['total_cost'] += reading['cost'] or 0.0
            device_data[device_name]['power_readings'].append(reading['power_watts'] or 0.0)
            device_data[device_name]['peak_power_watts'] = max(
                device_data[device_name]['peak_power_watts'], 
                reading['power_watts'] or 0.0
            )
        
        # Calculate averages and finalize device data
        devices = []
        total_energy_kwh = 0.0
        total_cost = 0.0
        peak_power_watts = 0.0
        active_devices = 0
        
        for device_name, data in device_data.items():
            if data['power_readings']:
                avg_power_watts = sum(data['power_readings']) / len(data['power_readings'])
                
                device_info = {
                    'device_name': device_name,
                    'device_id': device_name.lower().replace(' ', '_').replace('-', '_'),
                    'total_energy_kwh': round(data['total_energy_kwh'], 3),
                    'total_cost': round(data['total_cost'], 2),
                    'avg_power_watts': round(avg_power_watts, 2),
                    'peak_power_watts': round(data['peak_power_watts'], 2),
                    'status': self._get_device_status(avg_power_watts)
                }
                
                devices.append(device_info)
                total_energy_kwh += data['total_energy_kwh']
                total_cost += data['total_cost']
                peak_power_watts = max(peak_power_watts, data['peak_power_watts'])
                
                if avg_power_watts >= self.active_device_threshold:
                    active_devices += 1
        
        # Calculate projections
        if days_elapsed > 0:
            daily_avg = total_energy_kwh / days_elapsed
            projected_kwh = daily_avg * 30  # Project for 30 days
            projected_cost = projected_kwh * self.electricity_rate
        else:
            projected_kwh = total_energy_kwh
            projected_cost = total_cost
        
        conn.close()
        
        return {
            'month': f"{year:04d}-{month:02d}",
            'total_energy_kwh': round(total_energy_kwh, 3),
            'total_cost': round(total_cost, 2),
            'peak_power_watts': round(peak_power_watts, 2),
            'devices': devices,
            'active_devices': active_devices,
            'total_devices': len(devices),
            'days_elapsed': days_elapsed,
            'projected_kwh': round(projected_kwh, 1),
            'projected_cost': round(projected_cost, 2)
        }
    
    def get_current_power_summary(self) -> Dict:
        """
        Get current power summary for dashboard
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get latest power readings for each device
        cursor.execute("""
            SELECT 
                device_name,
                power_watts
            FROM energy_readings 
            WHERE timestamp IN (
                SELECT MAX(timestamp) 
                FROM energy_readings 
                GROUP BY device_name
            )
        """)
        
        readings = cursor.fetchall()
        
        if not readings:
            conn.close()
            return {
                'total_power_watts': 0.0,
                'daily_cost': 0.0,
                'monthly_estimate': 0.0,
                'active_devices': 0,
                'total_devices': 0
            }
        
        total_power_watts = sum(r['power_watts'] or 0 for r in readings)
        active_devices = sum(1 for r in readings if (r['power_watts'] or 0) >= self.active_device_threshold)
        
        # Calculate projected daily cost
        daily_energy_kwh = (total_power_watts * 24) / 1000
        daily_cost = daily_energy_kwh * self.electricity_rate
        monthly_estimate = daily_cost * 30
        
        conn.close()
        
        return {
            'total_power_watts': round(total_power_watts, 2),
            'daily_cost': round(daily_cost, 2),
            'monthly_estimate': round(monthly_estimate, 2),
            'active_devices': active_devices,
            'total_devices': len(readings)
        }
    
    def _get_device_status(self, power_watts: float) -> str:
        """Get device status based on power consumption"""
        if power_watts >= self.active_device_threshold:
            return "Active"
        elif power_watts >= self.standby_device_threshold:
            return "Standby"
        else:
            return "Off"
    
    def get_device_status_thresholds(self) -> Dict:
        """Get the thresholds used for device status classification"""
        return {
            'active_threshold': self.active_device_threshold,
            'standby_threshold': self.standby_device_threshold
        }

