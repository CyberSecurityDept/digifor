#!/bin/bash
# Wrapper script untuk menjalankan service dengan virtual environment aktif
# Script ini digunakan oleh systemd service

cd /home/digifor/digifor-v2
source venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info --no-access-log

