#!/bin/bash

# Forenlytic Backend - Quick Run Script
# Script ini memudahkan menjalankan aplikasi dari root directory

echo "Forenlytic Backend - Quick Run"
echo "================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Please run this script from the backend directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    ./scripts/setup.sh
    if [ $? -ne 0 ]; then
        echo "Setup failed. Please check the error messages above."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if database exists
if [ ! -f "data/forenlytic.db" ]; then
    echo "Database not found. Initializing..."
    python tools/init_db.py
    python tools/create_admin.py
fi

# Start the application
echo "Starting Forenlytic Backend..."
echo "Server: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
# echo "Admin: admin / admin123"
echo "================================"

python tools/run_dev.py
