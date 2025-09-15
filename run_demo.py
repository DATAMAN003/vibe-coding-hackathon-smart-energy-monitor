#!/usr/bin/env python3
"""Demo runner for Smart Energy Monitor"""

import asyncio
import threading
import time
import signal
import sys
from data_collector import EnergyDataCollector
from web_interface_fixed import app
import config

class DemoRunner:
    def __init__(self):
        self.collector = EnergyDataCollector(use_simulation=True)
        self.running = False
        
    def start_data_collection(self):
        """Start data collection in background thread"""
        def collection_loop():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            
            async def collect_data():
                print("🔌 Starting simulated data collection...")
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
        
        collection_thread = threading.Thread(target=collection_loop, daemon=True)
        collection_thread.start()
        return collection_thread
    
    def start_web_interface(self):
        """Start Flask web interface"""
        print(f"🌐 Starting web interface at http://localhost:{config.WEB_PORT}")
        app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False, use_reloader=False)
    
    def run_demo(self):
        """Run the complete demo"""
        print("🏠 Smart Energy Monitor Demo")
        print("=" * 50)
        print("This demo simulates a complete home energy monitoring system")
        print("with AI-powered insights.")
        print()
        
        self.running = True
        
        # Start data collection
        collection_thread = self.start_data_collection()
        
        # Give it a moment to collect some initial data
        print("⏳ Collecting initial data...")
        time.sleep(3)
        
        # Start web interface (this blocks)
        try:
            self.start_web_interface()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down demo...")
            self.running = False
            sys.exit(0)

def signal_handler(sig, frame):
    print("\n🛑 Demo interrupted")
    sys.exit(0)

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal_handler)
    
    demo = DemoRunner()
    demo.run_demo()