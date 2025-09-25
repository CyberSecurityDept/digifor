#!/bin/bash

# Forenlytic Backend Starter Script

echo "🚀 Starting Forenlytic Backend..."
echo "=" * 50

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the backend directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/uploads
mkdir -p data/analysis
mkdir -p data/reports
mkdir -p logs

# Check if database exists
if [ ! -f "data/digifor.db" ]; then
    echo "🗄️ Database not found. Initializing..."
    python tools/init_db.py
    python tools/create_admin.py
    echo "✅ Database initialized"
fi

# Start the application
echo "🎯 Starting FastAPI server..."
echo "🌐 Server will be available at: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "📚 ReDoc: http://localhost:8000/redoc"
echo "📄 Project Documentation: docs/INDEX.md"
# echo "👤 Default admin: admin / admin123"
echo "=" * 50

python tools/run_dev.py
