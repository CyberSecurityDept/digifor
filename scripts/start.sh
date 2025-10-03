#!/bin/bash
# Script untuk menjalankan server backend

echo "🚀 Starting Digital Forensics Backend Server"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "💡 Please run: python -m venv venv"
    echo "💡 Then run: source venv/bin/activate"
    echo "💡 Then run: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo "💡 Please run: pip install -r requirements.txt"
    exit 1
fi

# Run the server
echo "🚀 Starting server..."
echo "📡 Server will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health/health"
echo "=============================================="
echo "💡 Press Ctrl+C to stop the server"
echo "=============================================="

python run_dev.py
