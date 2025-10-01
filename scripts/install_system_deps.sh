#!/bin/bash

# Digital Forensics Backend - System Dependencies Installer
# Script untuk install system dependencies yang diperlukan

echo "🔧 Digital Forensics Backend - System Dependencies Installer"
echo "====================================================="

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "🍎 Detected macOS"
    echo "Installing system dependencies via Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo " Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install libmagic
    echo "📦 Installing libmagic..."
    brew install libmagic
    
    if [ $? -eq 0 ]; then
        echo "✅ libmagic installed successfully"
    else
        echo " Failed to install libmagic"
        exit 1
    fi

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 Detected Linux"
    
    # Detect package manager
    if command -v apt-get &> /dev/null; then
        echo "Installing system dependencies via apt-get..."
        sudo apt-get update
        sudo apt-get install -y libmagic1-dev
    elif command -v yum &> /dev/null; then
        echo "Installing system dependencies via yum..."
        sudo yum install -y file-devel
    elif command -v dnf &> /dev/null; then
        echo "Installing system dependencies via dnf..."
        sudo dnf install -y file-devel
    else
        echo " Unsupported package manager. Please install libmagic manually."
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ libmagic installed successfully"
    else
        echo " Failed to install libmagic"
        exit 1
    fi

else
    echo " Unsupported operating system: $OSTYPE"
    echo "Please install libmagic manually for your system."
    exit 1
fi

echo ""
echo "🎉 System dependencies installed successfully!"
echo "You can now run: ./run.sh"
