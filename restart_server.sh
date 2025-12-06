#!/bin/bash
echo "Stopping uvicorn server..."
pkill -9 -f uvicorn
sleep 2

echo "Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find venv -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find venv -name "*.pyc" -delete 2>/dev/null || true

echo "Starting server with PYTHONDONTWRITEBYTECODE..."
PYTHONDONTWRITEBYTECODE=1 python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
