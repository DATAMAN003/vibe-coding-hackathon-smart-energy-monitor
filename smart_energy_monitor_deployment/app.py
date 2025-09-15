#!/usr/bin/env python3
"""
Smart Energy Monitor - Main Application Entry Point

A standalone application for AI-powered home energy monitoring.
Run this file to start the complete system.
"""

import sys
import os
import argparse
import signal
import threading
import time
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_collector import EnergyDataCollector
from web_interface import app
from database import EnergyDatabase
import config

class SmartEnergyMonitorApp:
    """Main application class for Smart Energy Monitor"""
    
    def __init__(self):
        self.collector = None
        self.running = False
        self.collection_thread = None
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown on Ctrl+C"""
        def signal_handler(sig, frame):
            print("\n🛑 Shutting down Smart Energy Monitor...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start_data_collection(self, use_simulation=True):
        """Start data collection in background thread"""
        self.collector = EnergyDataCollector(use_simulation=use_simulation)
        
        def collection_loop():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            
            async def collect_data():
                print("🔌 Starting data collection...")
                while self.running:
                    try:
                        readings = await self.collector.collect_all_devices()
                        if readings:
                            self.collector.save_readings(readings)
                            print(f"📊 Collected {len(readings)} readings")
                        await asyncio.sleep(config.POLLING_INTERVAL)
                    except Exception as e:
                        print(f"❌ Collection error: {e}")
                        await asyncio.sleep(5)
            
            loop.run_until_complete(collect_data())
        
        self.collection_thread = threading.Thread(target=collection_loop, daemon=True)
        self.collection_thread.start()
    
    def start_web_interface(self, host="0.0.0.0", port=5000, debug=False):
        """Start the web interface"""
        print(f"🌐 Starting web interface at http://{host}:{port}")
        print("📱 Open your browser and navigate to the URL above")
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    
    def run_full_application(self, use_simulation=True, host="0.0.0.0", port=5000, debug=False):
        """Run the complete application with data collection and web interface"""
        print("🏠 Smart Energy Monitor")
        print("=" * 50)
        print("AI-powered home energy monitoring system")
        print("Categories: Local Agent + For Humanity")
        print()
        
        # Setup graceful shutdown
        self.setup_signal_handlers()
        
        # Initialize database
        print("🗄️  Initializing database...")
        db = EnergyDatabase()
        
        # Start data collection
        self.running = True
        self.start_data_collection(use_simulation)
        
        # Give data collection a moment to start
        print("⏳ Starting up...")
        time.sleep(2)
        
        # Start web interface (this blocks)
        try:
            self.start_web_interface(host, port, debug)
        except KeyboardInterrupt:
            self.stop()
    
    def run_data_collection_only(self, use_simulation=True):
        """Run only data collection without web interface"""
        print("🔌 Smart Energy Monitor - Data Collection Only")
        print("=" * 50)
        
        self.setup_signal_handlers()
        self.running = True
        
        collector = EnergyDataCollector(use_simulation=use_simulation)
        
        try:
            asyncio.run(collector.start_collection())
        except KeyboardInterrupt:
            print("\n🛑 Stopping data collection...")
    
    def run_web_only(self, host="0.0.0.0", port=5000, debug=False):
        """Run only web interface without data collection"""
        print("🌐 Smart Energy Monitor - Web Interface Only")
        print("=" * 50)
        
        self.setup_signal_handlers()
        self.start_web_interface(host, port, debug)
    
    def run_setup(self):
        """Run the setup process"""
        print("🔧 Smart Energy Monitor - Setup")
        print("=" * 50)
        
        from setup import main as setup_main
        setup_main()
    
    def stop(self):
        """Stop the application"""
        self.running = False
        if self.collector:
            self.collector.stop_collection()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Smart Energy Monitor - AI-powered home energy monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                          # Run full application with simulation
  python app.py --hardware               # Run with real hardware sensors
  python app.py --mode web --port 8080   # Run web interface only on port 8080
  python app.py --mode collect --hardware # Run data collection only with hardware
  python app.py --setup                  # Run setup wizard
        """
    )
    
    parser.add_argument('--mode', choices=['full', 'collect', 'web', 'setup'], 
                       default='full', help='Application mode (default: full)')
    parser.add_argument('--hardware', action='store_true', 
                       help='Use real hardware sensors instead of simulation')
    parser.add_argument('--host', default='0.0.0.0', 
                       help='Web interface host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, 
                       help='Web interface port (default: 5000)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode for web interface')
    parser.add_argument('--setup', action='store_true',
                       help='Run setup wizard (same as --mode setup)')
    
    args = parser.parse_args()
    
    # Handle --setup flag
    if args.setup:
        args.mode = 'setup'
    
    app_instance = SmartEnergyMonitorApp()
    use_simulation = not args.hardware
    
    try:
        if args.mode == 'full':
            app_instance.run_full_application(use_simulation, args.host, args.port, args.debug)
        elif args.mode == 'collect':
            app_instance.run_data_collection_only(use_simulation)
        elif args.mode == 'web':
            app_instance.run_web_only(args.host, args.port, args.debug)
        elif args.mode == 'setup':
            app_instance.run_setup()
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()