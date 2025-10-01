#!/bin/bash

# Digital Forensics Backend Setup Script

echo "🚀 Setting up Digital Forensics Backend..."

# Check if Python 3.8+ is installed
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo " Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/uploads
mkdir -p data/analysis
mkdir -p data/reports
mkdir -p logs
mkdir -p data/hash_db

# Initialize database
echo "🗄️ Initializing database..."
python tools/init_db.py

# Create admin user
echo "👤 Creating admin user..."
python tools/create_admin.py

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 To start the application:"
echo "   source venv/bin/activate"
echo "   python tools/run_dev.py"
echo ""
echo "📖 API Documentation will be available at:"
echo "   http://localhost:8000/docs"
echo ""
echo "📚 Project Documentation:"
echo "   docs/INDEX.md - Main documentation index"
echo "   docs/QUICK_START.md - Quick start guide"
echo "   docs/USAGE.md - Usage guide"
echo ""
echo "👤 Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  Please change the password after first login!"
