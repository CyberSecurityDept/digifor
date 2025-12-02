#!/bin/bash
# Script untuk menjalankan server backend

echo "Starting Digital Forensics Backend Server"
echo "=============================================="

if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then run: source venv/bin/activate"
    echo "Then run: pip install -r requirements.txt"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

if ! python -c "import fastapi" 2>/dev/null; then
    echo "Dependencies not installed!"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

echo "Starting server..."
echo "Server will be available at: http://172.15.1.207"
echo "API Documentation: http://172.15.1.207/docs"
echo "Health Check: http://172.15.1.207/health/health"
echo "=============================================="
echo "Press Ctrl+C to stop the server"
echo "=============================================="

python run_dev.py
