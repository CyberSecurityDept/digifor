#!/bin/bash

# Forenlytic Backend Start Script

echo "🚀 Starting Forenlytic Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if database exists
if [ ! -f "data/forenlytic.db" ]; then
    echo "🗄️ Database not found. Initializing..."
    python tools/init_db.py
fi

# Start the application
echo "🎯 Starting FastAPI server..."
python tools/run.py
