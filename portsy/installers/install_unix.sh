#!/bin/bash

echo "🚀 Installing Portsy..."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH."
    echo "Please install Python 3 from https://python.org"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install psutil requests
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Copy to /usr/local/bin (requires sudo)
echo "🔧 Installing portsy command..."
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    if [ -f "dist/Portsy.app/Contents/MacOS/Portsy" ]; then
        sudo cp dist/Portsy.app/Contents/MacOS/Portsy /usr/local/bin/portsy
    else
        sudo cp portsy.py /usr/local/bin/portsy
    fi
else
    # Linux
    sudo cp portsy.py /usr/local/bin/portsy
fi

sudo chmod +x /usr/local/bin/portsy

echo "✅ Installation complete!"
echo "Run: portsy --help"
