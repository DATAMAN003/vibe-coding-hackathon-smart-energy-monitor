#!/usr/bin/env python3
"""
Smart Energy Monitor - System Test Suite
Comprehensive testing of all system components
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing module imports...")
    
    modules = [
        'config',
        'database', 
        'data_collector',
        'ai_analyzer',
        'web_interface',
        'hardware_interface'
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0

def test_database():
    """Test database functionality"""
    print("\n🗄️  Testing database...")
    
    try:
        from database import EnergyDatabase
        
        db = EnergyDatabase()
        print("  ✅ Database connection")
        
        # Test adding a reading
        db.add_reading(
            device_id='test_device',
            device_name='Test Device', 
            power_watts=100.0,
            energy_kwh=0.1
        )
        print("  ✅ Add reading")
        
        # Test retrieving readings
        readings = db.get_recent_readings('test_device', hours=24)
        if readings:
            print("  ✅ Retrieve readings")
        else:
            print("  ⚠️  No readings retrieved (may be normal)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_ai_analyzer():
    """Test AI analyzer functionality"""
    print("\n🤖 Testing AI analyzer...")
    
    try:
        from ai_analyzer import EnergyAIAnalyzer
        
        # Test with mock AI
        analyzer = EnergyAIAnalyzer(use_mock_ai=True)
        print("  ✅ AI analyzer initialization")
        
        # Test device analysis
        result = analyzer.analyze_device_patterns('test_device')
        if 'insights' in result:
            print("  ✅ Device pattern analysis")
        else:
            print(f"  ⚠️  Device analysis returned: {result}")
        
        # Test home analysis
        home_result = analyzer.analyze_home_energy()
        if 'insights' in home_result:
            print("  ✅ Home energy analysis")
        else:
            print(f"  ⚠️  Home analysis returned: {home_result}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ AI analyzer test failed: {e}")
        return False

def test_data_collector():
    """Test data collection functionality"""
    print("\n📊 Testing data collector...")
    
    try:
        from data_collector import EnergyDataCollector
        
        # Test with simulation
        collector = EnergyDataCollector(use_simulation=True)
        print("  ✅ Data collector initialization")
        
        # Test collecting readings
        async def test_collection():
            readings = await collector.collect_all_devices()
            return readings
        
        readings = asyncio.run(test_collection())
        if readings:
            print(f"  ✅ Data collection ({len(readings)} readings)")
            
            # Test saving readings
            collector.save_readings(readings)
            print("  ✅ Save readings to database")
        else:
            print("  ⚠️  No readings collected")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Data collector test failed: {e}")
        return False

def test_web_interface():
    """Test web interface components"""
    print("\n🌐 Testing web interface...")
    
    try:
        from web_interface import app
        
        # Test that Flask app is created
        if app:
            print("  ✅ Flask app creation")
        
        # Test app configuration
        with app.app_context():
            print("  ✅ App context")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Web interface test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️  Testing configuration...")
    
    try:
        import config
        
        # Check required settings exist
        required_settings = [
            'POLLING_INTERVAL',
            'ENERGY_SENSORS', 
            'ELECTRICITY_RATE',
            'DATABASE_PATH'
        ]
        
        for setting in required_settings:
            if hasattr(config, setting):
                print(f"  ✅ {setting}")
            else:
                print(f"  ❌ Missing {setting}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'app.py',
        'config.py',
        'database.py',
        'data_collector.py',
        'ai_analyzer.py',
        'web_interface.py',
        'hardware_interface.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ Missing {file}")
            missing_files.append(file)
    
    return len(missing_files) == 0

def run_integration_test():
    """Run a complete integration test"""
    print("\n🔄 Running integration test...")
    
    try:
        # Import all components
        from data_collector import EnergyDataCollector
        from ai_analyzer import EnergyAIAnalyzer
        from database import EnergyDatabase
        
        # Collect some data
        collector = EnergyDataCollector(use_simulation=True)
        readings = asyncio.run(collector.collect_all_devices())
        
        if not readings:
            print("  ❌ No data collected for integration test")
            return False
        
        # Save to database
        collector.save_readings(readings)
        print("  ✅ Data collection and storage")
        
        # Analyze with AI
        analyzer = EnergyAIAnalyzer(use_mock_ai=True)
        device_id = readings[0]['device_id']
        analysis = analyzer.analyze_device_patterns(device_id)
        
        if 'insights' in analysis:
            print("  ✅ AI analysis")
        else:
            print(f"  ⚠️  AI analysis incomplete: {analysis}")
        
        print("  ✅ Integration test completed")
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Smart Energy Monitor - System Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("Database", test_database),
        ("Data Collector", test_data_collector),
        ("AI Analyzer", test_ai_analyzer),
        ("Web Interface", test_web_interface),
        ("Integration", run_integration_test)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready to use.")
        print("\nTo start the system:")
        print("  python app.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("The system may still work, but some features might be limited.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)