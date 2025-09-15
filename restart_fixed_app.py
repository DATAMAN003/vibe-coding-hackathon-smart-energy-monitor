#!/usr/bin/env python3
"""
Restart with fixed app
"""

import os
import subprocess
import time

def stop_processes():
    """Stop Python processes"""
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
        print("🛑 Stopped existing processes")
        time.sleep(2)
    except:
        print("ℹ️  No processes to stop")

def main():
    print("🔄 RESTARTING WITH FIXES")
    print("=" * 30)
    
    stop_processes()
    
    # Remove database to start fresh
    if os.path.exists("energy_monitor.db"):
        os.remove("energy_monitor.db")
        print("🗑️  Removed old database")
    
    print("🚀 Starting fixed app...")
    
    # Start the fixed app
    from simple_energy_app import main as run_app
    run_app()

if __name__ == "__main__":
    main()