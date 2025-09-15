#!/bin/bash
# Smart Energy Monitor - Linux/Mac Startup Script

echo "🏠 Smart Energy Monitor"
echo "====================================================="
echo "AI-powered home energy monitoring system"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ using your package manager"
    exit 1
fi

# Change to script directory
cd "$(dirname "$0")"

# Check if this is first run
if [ ! -f "data/energy_monitor.db" ]; then
    echo "🔧 First run detected - running setup..."
    python3 install.py
    echo ""
fi

# Start the application
echo "🚀 Starting Smart Energy Monitor..."
echo "📱 Open your browser to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop"
echo ""

python3 app.py