#!/usr/bin/env python3
"""Setup script for Smart Energy Monitor"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def detect_platform():
    """Detect the platform we're running on"""
    import platform
    
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    is_raspberry_pi = os.path.exists('/proc/device-tree/model')
    is_arm = 'arm' in machine or 'aarch64' in machine
    
    return {
        'system': system,
        'machine': machine,
        'is_raspberry_pi': is_raspberry_pi,
        'is_arm': is_arm,
        'is_windows': system == 'windows',
        'is_macos': system == 'darwin',
        'is_linux': system == 'linux'
    }

def install_dependencies():
    """Install required Python packages with platform-specific handling"""
    platform_info = detect_platform()
    print(f"📦 Installing dependencies for {platform_info['system']} ({platform_info['machine']})...")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install from requirements.txt if it exists
    if Path("requirements.txt").exists():
        command = f"{sys.executable} -m pip install -r requirements.txt"
        if run_command(command, "Installing core dependencies from requirements.txt"):
            print("✅ Core dependencies installed")
        else:
            print("⚠️  Some dependencies may have failed - continuing with manual installation")
    
    # Platform-specific AI packages
    print("\n🤖 Installing AI packages...")
    
    # Ask user if they want AI features
    try:
        install_ai = input("Install AI features? (y/n, default=y): ").lower()
        if install_ai in ['', 'y', 'yes']:
            install_ai_packages(platform_info)
        else:
            print("⏭️  Skipping AI packages - you can install later with: pip install -r requirements-ai.txt")
    except KeyboardInterrupt:
        print("\n⏭️  Skipping AI packages")

def install_ai_packages(platform_info):
    """Install AI packages with platform-specific optimizations"""
    if Path("requirements-ai.txt").exists():
        print("📋 Installing from requirements-ai.txt...")
        
        if platform_info['is_raspberry_pi']:
            print("🍓 Raspberry Pi detected - using CPU-optimized packages")
            # For Raspberry Pi, we might want to use lighter alternatives
            command = f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
            run_command(command, "Installing PyTorch (CPU-only for Raspberry Pi)")
            
            command = f"{sys.executable} -m pip install transformers accelerate"
            run_command(command, "Installing Transformers and Accelerate")
            
        elif platform_info['is_arm'] and platform_info['is_macos']:
            print("🍎 Apple Silicon Mac detected - using optimized packages")
            command = f"{sys.executable} -m pip install torch torchvision torchaudio"
            run_command(command, "Installing PyTorch (Apple Silicon optimized)")
            
            command = f"{sys.executable} -m pip install transformers accelerate"
            run_command(command, "Installing Transformers and Accelerate")
            
        else:
            # Standard installation for x86/x64 systems
            command = f"{sys.executable} -m pip install -r requirements-ai.txt"
            if not run_command(command, "Installing AI dependencies"):
                print("⚠️  AI package installation failed - you can install manually later")
    else:
        print("⚠️  requirements-ai.txt not found - skipping AI packages")

def create_directories():
    """Create necessary directories"""
    directories = ["data", "logs", "static", "templates"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

def initialize_database():
    """Initialize the SQLite database"""
    try:
        from database import EnergyDatabase
        db = EnergyDatabase()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_sample_config():
    """Create a sample configuration file"""
    sample_config = """# Sample device configuration
# Copy this to config.py and update with your actual device IPs

SMART_PLUGS = {
    "living_room_tv": {
        "type": "kasa",
        "ip": "192.168.1.100",  # Update with your device IP
        "name": "Living Room TV"
    },
    "kitchen_microwave": {
        "type": "kasa", 
        "ip": "192.168.1.101",  # Update with your device IP
        "name": "Kitchen Microwave"
    },
    # Add more devices as needed
}

# Update these settings for your location
ELECTRICITY_RATE = 0.12  # dollars per kWh
CURRENCY_SYMBOL = "$"
"""
    
    with open("config_sample.py", "w") as f:
        f.write(sample_config)
    
    print("📝 Created config_sample.py - copy to config.py and update with your device IPs")

def main():
    """Main setup function"""
    print("🏠 Smart Energy Monitor Setup")
    print("=" * 40)
    
    platform_info = detect_platform()
    print(f"🖥️  Platform: {platform_info['system']} on {platform_info['machine']}")
    
    if platform_info['is_raspberry_pi']:
        print("🍓 Raspberry Pi detected - optimizing for embedded system")
    
    if not check_python_version():
        return False
    
    create_directories()
    install_dependencies()
    
    if initialize_database():
        print("✅ Database setup complete")
    else:
        print("⚠️  Database setup had issues - you may need to run this again")
    
    create_sample_config()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Copy config_sample.py to config.py and update with your settings")
    print("2. Test the system: python app.py --mode collect")
    print("3. Start full monitoring: python app.py")
    print("4. Open http://localhost:5000 in your browser")
    
    if platform_info['is_raspberry_pi']:
        print("\n🍓 Raspberry Pi specific notes:")
        print("- For hardware sensors, see HARDWARE_GUIDE.md")
        print("- Consider using simulation mode for initial testing")
        print("- AI features may be slower on Pi - consider using mock AI")
    
    return True

if __name__ == "__main__":
    main()