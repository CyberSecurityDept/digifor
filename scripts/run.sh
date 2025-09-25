#!/bin/bash

# Forenlytic Backend - Quick Run Script
# Script ini memudahkan menjalankan aplikasi dari root directory

echo "Forenlytic Backend - Quick Run"
echo "==============================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Please run this script from the backend directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "Created .env from env.example"
        echo "Please edit .env file with your configuration before running again."
        echo "   nano .env  # Edit configuration"
        exit 1
    else
        echo "Error: env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please check Python installation."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Please check requirements.txt"
    exit 1
fi

# Check environment variables
echo "Checking environment configuration..."
python tools/check_env.py >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Environment configuration check failed."
    echo "Please check your .env file and ensure all required variables are set."
    echo "   See docs/COMPLETE_ENVIRONMENT_GUIDE.md for detailed configuration guide."
    exit 1
fi

# Check database connection
echo "Checking database connection..."
python -c "from app.database import engine; print('Database connection successful')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Database connection failed. Attempting to setup PostgreSQL..."
    python tools/setup_postgres.py >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "PostgreSQL setup failed. Please check your database configuration."
        echo "   See docs/COMPLETE_ENVIRONMENT_GUIDE.md for PostgreSQL setup guide."
        exit 1
    fi
fi

# Run the application
python tools/run_dev.py
