#!/bin/bash

# Script untuk update database connection ke server remote
# Usage: ./scripts/update-db-to-server.sh [SERVER_IP] [PORT] [USER] [PASSWORD] [DATABASE]

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Default values
SERVER_IP="${1:-172.15.2.105}"
PORT="${2:-5432}"
USER="${3:-digifor}"
PASSWORD="${4:-passwordD*8}"
DATABASE="${5:-db_forensics}"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: File $ENV_FILE tidak ditemukan!"
    exit 1
fi

echo "=========================================="
echo "Update Database Connection to Server"
echo "=========================================="
echo ""
echo "Server IP: $SERVER_IP"
echo "Port: $PORT"
echo "User: $USER"
echo "Database: $DATABASE"
echo ""
echo "Apakah Anda yakin ingin mengupdate .env file? (y/n)"
read -r confirmation

if [ "$confirmation" != "y" ] && [ "$confirmation" != "Y" ]; then
    echo "❌ Update dibatalkan"
    exit 0
fi

# Backup .env file
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "Backup created: ${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# Update DATABASE_URL
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://${USER}:${PASSWORD}@${SERVER_IP}:${PORT}/${DATABASE}|g" "$ENV_FILE"

# Update POSTGRES_HOST
sed -i "s|^POSTGRES_HOST=.*|POSTGRES_HOST=${SERVER_IP}|g" "$ENV_FILE"

# Update POSTGRES_PORT
sed -i "s|^POSTGRES_PORT=.*|POSTGRES_PORT=${PORT}|g" "$ENV_FILE"

# Update POSTGRES_USER
sed -i "s|^POSTGRES_USER=.*|POSTGRES_USER=${USER}|g" "$ENV_FILE"

# Update POSTGRES_PASSWORD
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${PASSWORD}|g" "$ENV_FILE"

# Update POSTGRES_DB
sed -i "s|^POSTGRES_DB=.*|POSTGRES_DB=${DATABASE}|g" "$ENV_FILE"

echo ""
echo "Update selesai!"
echo ""
echo "File .env telah diupdate dengan konfigurasi:"
echo "  DATABASE_URL=postgresql://${USER}:****@${SERVER_IP}:${PORT}/${DATABASE}"
echo "  POSTGRES_HOST=${SERVER_IP}"
echo "  POSTGRES_PORT=${PORT}"
echo "  POSTGRES_USER=${USER}"
echo "  POSTGRES_PASSWORD=****"
echo "  POSTGRES_DB=${DATABASE}"
echo ""
echo "Catatan: Password disembunyikan untuk keamanan"
echo ""
echo "Untuk test koneksi, jalankan:"
echo "  python3 scripts/check-db-connection.py"

