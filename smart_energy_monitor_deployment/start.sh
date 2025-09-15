#!/bin/bash

# Smart Energy Monitor vv1.0.0 Launcher
echo "🏠 Smart Energy Monitor vv1.0.0"
echo "================================================"
echo "AI-powered home energy monitoring system"
echo "Categories: Local Agent + For Humanity"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

# Check if this is first run
if [ ! -d "data" ]; then
    echo "🔧 First run detected - running setup..."
    python3 install.py
    if [ $? -ne 0 ]; then
        echo "❌ Setup failed"
        exit 1
    fi
fi

echo "🚀 Starting Smart Energy Monitor..."
echo "Open your browser to: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
