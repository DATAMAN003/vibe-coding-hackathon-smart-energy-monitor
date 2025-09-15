#!/usr/bin/env python3
"""
Smart Energy Monitor vv1.0.0 - Quick Install
One-click installation and launch
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🏠 Smart Energy Monitor vv1.0.0 - Quick Install")
    print("=" * 60)
    print("AI-powered home energy monitoring system")
    print("Categories: Local Agent + For Humanity")
    print()
    
    try:
        # Run installation
        print("🔧 Running installation...")
        result = subprocess.run([sys.executable, "install.py"], cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            print("❌ Installation failed")
            return False
        
        # Ask if user wants to start immediately
        try:
            start_now = input("\n🚀 Start Smart Energy Monitor now? (y/n, default=y): ").lower()
            if start_now in ['', 'y', 'yes']:
                print("\n🌐 Starting Smart Energy Monitor...")
                print("Open your browser to: http://localhost:5000")
                print("Press Ctrl+C to stop")
                print()
                
                subprocess.run([sys.executable, "app.py"], cwd=Path(__file__).parent)
        except KeyboardInterrupt:
            print("\n⏹️  Installation complete. Run 'python app.py' to start.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        input("Press Enter to exit...")
        sys.exit(1)
