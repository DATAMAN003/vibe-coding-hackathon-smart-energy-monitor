#!/usr/bin/env python3
"""
Complete Energy Monitor App - Runs both simulation and web interface
"""

import sys
import os
import threading
import time
import signal
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realistic_simulator import RealisticDeviceSimulator
from database import EnergyDatabase
from web_interface_fixed import app
import config

class CompleteEnergyMonitorApp:
    """Complete app that runs both simulation and web interface"""
    
    def __init__(self):
        self.simulator = RealisticDeviceSimulator()
        self.db = EnergyDatabase()
        self.running = False
        self.simulation_thread = None
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown"""
        def signal_handler(sig, frame):
            print("\n🛑 Stopping Complete Energy Monitor App...")
            self.running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run_simulation_loop(self):
        """Background simulation loop"""
        print("🔄 Starting background device simulation...")
        cycle_count = 0
        
        while self.running:
            try:
                # Get realistic readings from all devices
                readings = self.simulator.simulate_all_devices()
                
                # Save to database
                for reading in readings:
                    self.db.add_reading(
                        device_id=reading['device_id'],
                        device_name=reading['device_name'],
                        power_watts=reading['power_watts'],
                        voltage=reading['voltage'],
                        current=reading['current_amps'],
                        energy_kwh=reading['energy_kwh']
                    )
                
                cycle_count += 1
                
                # Log current status (less verbose for web interface)
                if cycle_count % 5 == 0:  # Log every 5 cycles (5 minutes)
                    current_time = datetime.now().strftime("%H:%M:%S")
                    total_power = sum(r['power_watts'] for r in readings)
                    active_devices = len([r for r in readings if r['status'] != 'standby'])
                    
                    print(f"📊 {current_time} | Simulation Update #{cycle_count} | {total_power:.0f}W | {active_devices}/7 active")
                
                # Wait for next update
                time.sleep(config.POLLING_INTERVAL)
                
            except Exception as e:
                print(f"❌ Simulation error: {e}")
                time.sleep(5)
    
    def start_simulation(self):
        """Start simulation in background thread"""
        self.running = True
        self.simulation_thread = threading.Thread(target=self.run_simulation_loop, daemon=True)
        self.simulation_thread.start()
    
    def start_web_interface(self, host="0.0.0.0", port=5000):
        """Start the web interface"""
        print(f"🌐 Starting web interface at http://{host}:{port}")
        print("📱 Dashboard features:")
        print("   • Real-time device monitoring")
        print("   • Live device state changes")
        print("   • AI insights and analytics")
        print("   • Cost tracking and projections")
        print()
        
        # Start Flask app (this blocks)
        app.run(host=host, port=port, debug=False, use_reloader=False)
    
    def run_complete_app(self, host="0.0.0.0", port=5000):
        """Run the complete application"""
        print("🏠 Complete Smart Energy Monitor")
        print("=" * 50)
        print("✅ Live device simulation + Web dashboard")
        print("🔄 Devices switch realistically based on time patterns")
        print("📊 Dashboard updates automatically every 30 seconds")
        print("🎯 All data synchronized and accurate")
        print()
        
        # Setup graceful shutdown
        self.setup_signal_handlers()
        
        # Start background simulation
        self.start_simulation()
        
        # Give simulation a moment to start
        time.sleep(2)
        
        # Start web interface (this blocks)
        try:
            self.start_web_interface(host, port)
        except KeyboardInterrupt:
            self.running = False
            print("\n🛑 Complete app stopped by user")

def main():
    """Main entry point"""
    app_instance = CompleteEnergyMonitorApp()
    
    try:
        app_instance.run_complete_app()
    except KeyboardInterrupt:
        print("\n🛑 Complete Energy Monitor stopped by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()