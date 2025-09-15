# Smart Energy Monitor vv1.0.0 - Deployment Package

## 🚀 Quick Start

### Windows
1. Double-click `start.bat`
2. Open browser to http://localhost:5000

### Linux/Mac
1. Run `./start.sh` or `bash start.sh`
2. Open browser to http://localhost:5000

### Alternative
1. Run `python quick_install.py` for guided setup
2. Or manually: `python install.py` then `python app.py`

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, Linux, macOS
- **Memory**: 512MB RAM minimum (1GB recommended)
- **Storage**: 100MB free space
- **Network**: Optional (for smart plug integration)

## 🏆 Hackathon Categories

- **Primary**: Local Agent - 100% offline operation
- **Secondary**: For Humanity - Energy conservation and cost savings

## ✨ Features

- Real-time energy monitoring
- AI-powered analysis and insights
- Web-based dashboard
- Hardware sensor support
- Privacy-first design (100% local)
- gpt-oss ready

## 🔧 Manual Installation

If the automatic installers don't work:

```bash
# Install core dependencies
pip install -r requirements.txt

# Optional: Install AI features
pip install -r requirements-ai.txt

# Optional: Install hardware support (Raspberry Pi)
# pip install spidev RPi.GPIO gpiozero

# Initialize database and test system
python install.py

# Start the application
python app.py
```

## 📚 Documentation

- `README.md` - Complete user guide
- `HARDWARE_GUIDE.md` - Hardware setup instructions
- `SYSTEM_OVERVIEW.md` - Technical architecture overview

## 🆘 Troubleshooting

1. **Python not found**: Install Python 3.8+ from python.org
2. **Permission errors**: Run as administrator/sudo
3. **Port 5000 in use**: The app will try alternative ports
4. **No devices shown**: Check config.py for device settings

## 🌐 Web Interface

Once running, access the dashboard at:
- http://localhost:5000 (local access)
- http://YOUR_IP:5000 (network access)

## 📞 Support

- Check the logs in the `logs/` directory
- Run `python test_system.py` to diagnose issues
- Review documentation files for detailed help

---

**Smart Energy Monitor** - Helping reduce energy consumption with AI-powered insights
