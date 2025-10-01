#!/bin/bash

# Digital Forensics Backend - Production Run Script
# Production-ready script with full validation

echo "Digital Forensics Backend - Production Mode"
echo "==================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Please run this script from the backend directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Production requires explicit configuration."
    echo "Please create .env file with your production configuration."
    echo "   See docs/COMPLETE_ENVIRONMENT_GUIDE.md for configuration guide."
    exit 1
fi

# Check file permissions
echo "Checking file permissions..."
if [ "$(stat -c %a .env 2>/dev/null || stat -f %A .env 2>/dev/null)" != "600" ]; then
    echo "Setting secure permissions for .env file..."
    chmod 600 .env
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Install/update dependencies
echo "Installing production dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies."
    exit 1
fi

# Full environment validation
echo "Running full environment validation..."
python tools/check_env.py >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Environment validation failed."
    echo "Please check your .env file and ensure all required variables are set."
    exit 1
fi

# Database connection test
echo "Testing database connection..."
python -c "from app.database import engine; print('Database connection successful')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Database connection failed. Please check your database configuration."
    exit 1
fi

# Security checks
echo "Running security checks..."
python -c "
from app.config import settings
import sys

# Check for production security
if settings.debug:
    print('WARNING: DEBUG mode is enabled in production!')
    print('   Consider setting DEBUG=False for production.')

if len(settings.secret_key) < 32:
    print('ERROR: SECRET_KEY is too short for production!')
    print('   Minimum 32 characters required.')
    sys.exit(1)

if len(settings.encryption_key) < 32:
    print('ERROR: ENCRYPTION_KEY is too short for production!')
    print('   Minimum 32 characters required.')
    sys.exit(1)

print('Security checks passed')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Security validation failed. Please check your configuration."
    exit 1
fi

# Run the application in production mode
python tools/run.py
