#!/usr/bin/env python3
"""
Smart Energy Monitor - One-click installer
This script sets up the complete Smart Energy Monitor system
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print installation banner"""
    print("""
🏠 Smart Energy Monitor Installer
==================================
AI-powered home energy monitoring system
Categories: Local Agent + For Humanity

This installer will:
✅ Check system requirements
✅ Install Python dependencies  
✅ Set up database
✅ Create configuration files
✅ Test the installation
""")

def check_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Please upgrade Python.")
        return False
    print(f"✅ Python {sys.version} detected")
    
    # Check pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip is available")
    except subprocess.CalledProcessError:
        print("❌ pip not found. Please install pip.")
        return False
    
    return True

def install_system():
    """Run the main installation"""
    print("\n🚀 Starting installation...")
    
    try:
        # Run setup.py
        result = subprocess.run([sys.executable, "setup.py"], 
                              cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Installation completed successfully!")
            return True
        else:
            print("❌ Installation encountered errors")
            return False
            
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        sys.path.insert(0, str(Path(__file__).parent))
        
        import config
        from database import EnergyDatabase
        from ai_analyzer import EnergyAIAnalyzer
        
        print("✅ Core modules imported successfully")
        
        # Test database
        db = EnergyDatabase()
        print("✅ Database connection works")
        
        # Test AI analyzer
        analyzer = EnergyAIAnalyzer(use_mock_ai=True)
        print("✅ AI analyzer initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def show_next_steps():
    """Show what to do next"""
    print("""
🎉 Installation Complete!

Next Steps:
1️⃣  Configure your devices:
   • Copy config_sample.py to config.py
   • Update with your smart plug IPs or sensor settings

2️⃣  Test data collection:
   python app.py --mode collect

3️⃣  Start the full system:
   python app.py

4️⃣  Open your browser to:
   http://localhost:5000

📚 Documentation:
   • README.md - Getting started guide
   • HARDWARE_GUIDE.md - Hardware setup instructions
   • config.py - Configuration options

🆘 Need help?
   • Check the logs in the logs/ directory
   • Run with --debug for more information
   • Review the documentation files
""")

def main():
    """Main installer function"""
    print_banner()
    
    if not check_requirements():
        print("\n❌ System requirements not met. Please fix the issues above.")
        return False
    
    if not install_system():
        print("\n❌ Installation failed. Please check the error messages above.")
        return False
    
    if not test_installation():
        print("\n⚠️  Installation completed but tests failed. The system may still work.")
    
    show_next_steps()
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)