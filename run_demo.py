#!/usr/bin/env python3
"""
Simple Energy Monitor App - Clean, working solution
"""

import os
import sys
import sqlite3
import threading
import time
import signal
from datetime import datetime
import random

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_interface_fixed import app
import config

class SimpleEnergyApp:
    """Simple energy monitor with live simulation"""
    
    def __init__(self):
        self.running = False
        self.simulation_thread = None
        self.setup_fresh_database()
        
    def setup_fresh_database(self):
        """Create fresh database with today's data"""
        # Remove any existing databases
        for db_file in ["energy_monitor.db", "realistic_energy_monitor.db", "fresh_energy_monitor.db"]:
            if os.path.exists(db_file):
                os.remove(db_file)
        
        # Create fresh database in the correct location
        import config
        db_path = str(config.DATABASE_PATH)  # Use config path: data/energy_monitor.db
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS energy_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                device_name TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                power_watts REAL NOT NULL,
                voltage REAL,
                current REAL,
                energy_kwh REAL,
                cost REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                device_name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                location TEXT,
                ip_address TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add exactly 7 devices and initial readings with TODAY'S date
        devices = [
            ("living_room_tv", "Living Room TV", "Living Room"),
            ("kitchen_microwave", "Kitchen Microwave", "Kitchen"),
            ("kitchen_fridge", "Kitchen Fridge", "Kitchen"),
            ("bedroom_ac", "Bedroom AC", "Bedroom"),
            ("office_computer", "Home Office Computer", "Office"),
            ("laundry_washer", "Washing Machine", "Laundry Room"),
            ("laundry_dryer", "Electric Dryer", "Laundry Room")
        ]
        
        # Clear any existing data first
        cursor.execute("DELETE FROM devices")
        cursor.execute("DELETE FROM energy_readings")
        
        for device_id, device_name, location in devices:
            # Add device
            cursor.execute("""
                INSERT INTO devices 
                (device_id, device_name, device_type, location, ip_address)
                VALUES (?, ?, 'smart_plug', ?, '192.168.1.100')
            """, (device_id, device_name, location))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Fresh database created: {db_path}")
        print(f"📅 Starting date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    def get_realistic_power(self, device_name, hour):
        """Get realistic power consumption based on device and time"""
        current_hour = datetime.now().hour
        
        # Device-specific realistic patterns
        if "TV" in device_name:
            if 19 <= current_hour <= 23:  # Evening TV time
                return random.uniform(120, 180)
            elif 7 <= current_hour <= 9:  # Morning news
                return random.uniform(80, 120)
            else:
                return random.uniform(2, 5)  # Standby
                
        elif "Fridge" in device_name:
            # Fridge cycles on/off
            return random.uniform(80, 200)
            
        elif "AC" in device_name:
            if 12 <= current_hour <= 18:  # Hot afternoon
                return random.uniform(1200, 2000)
            elif 20 <= current_hour <= 6:  # Night cooling
                return random.uniform(800, 1200)
            else:
                return random.uniform(5, 15)  # Standby
                
        elif "Computer" in device_name:
            if 8 <= current_hour <= 18:  # Work hours
                return random.uniform(200, 400)
            elif 19 <= current_hour <= 22:  # Evening use
                return random.uniform(150, 300)
            else:
                return random.uniform(5, 15)  # Sleep mode
                
        elif "Microwave" in device_name:
            # Microwave only on when cooking
            if random.random() < 0.05:  # 5% chance of being on
                return random.uniform(800, 1200)
            else:
                return random.uniform(1, 3)  # Standby
                
        elif "Washing" in device_name:
            # Washing machine cycles
            if random.random() < 0.1:  # 10% chance of running
                return random.uniform(400, 600)
            else:
                return random.uniform(2, 5)  # Standby
                
        elif "Dryer" in device_name:
            # Dryer cycles
            if random.random() < 0.08:  # 8% chance of running
                return random.uniform(2000, 3000)
            else:
                return random.uniform(3, 8)  # Standby
        
        # Default
        return random.uniform(10, 50)
    
    def update_device_readings(self):
        """Update all device readings in database"""
        conn = sqlite3.connect(str(config.DATABASE_PATH))
        cursor = conn.cursor()
        
        # Get all devices
        cursor.execute("SELECT device_id, device_name FROM devices")
        devices = cursor.fetchall()
        
        current_time = datetime.now()
        
        for device_id, device_name in devices:
            # Get realistic power for this device at this time
            power = self.get_realistic_power(device_name, current_time.hour)
            
            # Calculate other values
            voltage = 120.0
            current_amps = power / voltage
            # Energy for this reading (1 minute = 1/60 hour)
            energy_kwh = (power / 1000.0) * (1/60)  # kWh for 1 minute
            cost = energy_kwh * config.ELECTRICITY_RATE
            
            # Insert reading with current timestamp
            cursor.execute("""
                INSERT INTO energy_readings 
                (device_id, device_name, timestamp, power_watts, voltage, current, energy_kwh, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (device_id, device_name, current_time.isoformat(), power, voltage, current_amps, energy_kwh, cost))
        
        conn.commit()
        conn.close()
    
    def simulation_loop(self):
        """Background simulation loop"""
        cycle = 0
        while self.running:
            try:
                self.update_device_readings()
                cycle += 1
                
                if cycle % 5 == 0:  # Log every 5 cycles
                    print(f"📊 Simulation cycle #{cycle} - Database updated with realistic device states")
                
                time.sleep(60)  # Update every minute
                
            except Exception as e:
                print(f"❌ Simulation error: {e}")
                time.sleep(5)
    
    def start_simulation(self):
        """Start background simulation"""
        self.running = True
        self.simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
        self.simulation_thread.start()
        print("🔄 Background simulation started - devices will switch realistically")
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown"""
        def signal_handler(sig, frame):
            print("\n🛑 Stopping Simple Energy Monitor...")
            self.running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run(self, host="0.0.0.0", port=5000):
        """Run the complete app"""
        print("🏠 Simple Smart Energy Monitor")
        print("=" * 40)
        print("✅ Fresh database with today's date")
        print("🔄 Live device simulation")
        print("📊 Dashboard auto-refreshes every 30 seconds")
        print("🎯 All data synchronized")
        print()
        
        self.setup_signal_handlers()
        
        # Add initial readings
        self.update_device_readings()
        
        # Start background simulation
        self.start_simulation()
        
        # Start web interface
        print(f"🌐 Starting web interface at http://{host}:{port}")
        print("📱 Navigate to http://localhost:5000 to see the dashboard")
        print()
        
        try:
            app.run(host=host, port=port, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            self.running = False

def main():
    """Main entry point"""
    app_instance = SimpleEnergyApp()
    app_instance.run()

if __name__ == '__main__':
    main()