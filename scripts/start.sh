#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

PROJECT_DIR="/home/me/Documents/digital-forensics-v2/digifor"
VENV_DIR="$PROJECT_DIR/venv"
REQ_FILE="$PROJECT_DIR/requirements.txt"

cd "$PROJECT_DIR" || exit 1

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "ERROR: Virtual environment not found at $VENV_DIR"
    exit 1
fi

source "$VENV_DIR/bin/activate"

MISSING=0
while IFS= read -r pkg || [ -n "$pkg" ]; do
    [[ "$pkg" =~ ^#.*$ || -z "$pkg" ]] && continue
    PKG_NAME=$(echo "$pkg" | cut -d= -f1)
    pip show "$PKG_NAME" > /dev/null 2>&1 || MISSING=1
done < "$REQ_FILE"

if [ $MISSING -eq 1 ]; then
    echo "Installing missing dependencies..."
    pip install -r "$REQ_FILE"
else
    echo "All requirements already installed."
fi

python -m app.auth.seed

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
