#!/bin/bash

# Forenlytic Backend - Development Run Script
# Simple script for development with minimal checks

echo "Forenlytic Backend - Development Mode"
echo "====================================="

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
        echo "Please edit .env file with your configuration:"
        echo "   nano .env"
        exit 1
    else
        echo "Error: env.example not found."
        exit 1
    fi
fi

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run ./run.sh first for full setup."
fi

# Quick environment check
echo "Quick environment check..."
python -c "from app.config import settings; print('Environment loaded successfully')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Environment configuration error. Please check your .env file."
    echo "Run: python tools/check_env.py"
    exit 1
fi

# Run the application
python tools/run_dev.py
