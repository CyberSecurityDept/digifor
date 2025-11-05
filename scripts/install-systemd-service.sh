#!/bin/bash
# Script untuk menginstall systemd service untuk Digital Forensics API

echo "=========================================="
echo "Installing Digital Forensics Systemd Service"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: Script ini harus dijalankan dengan sudo"
    echo "Usage: sudo ./install-systemd-service.sh"
    exit 1
fi

SERVICE_FILE="digifor-v2.service"
PROJECT_DIR="/home/digifor/digifor-v2"
SYSTEMD_DIR="/etc/systemd/system"

# Check if service file exists
if [ ! -f "$PROJECT_DIR/$SERVICE_FILE" ]; then
    echo "Error: Service file tidak ditemukan di $PROJECT_DIR/$SERVICE_FILE"
    exit 1
fi

# Copy service file to systemd directory
echo "Copying service file to $SYSTEMD_DIR..."
cp "$PROJECT_DIR/$SERVICE_FILE" "$SYSTEMD_DIR/$SERVICE_FILE"

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable service to start on boot
echo "Enabling service to start on boot..."
systemctl enable digifor-v2.service

echo ""
echo "=========================================="
echo "Service berhasil diinstall!"
echo "=========================================="
echo ""
echo "Perintah yang bisa digunakan:"
echo "  sudo systemctl start digifor-v2    # Start service"
echo "  sudo systemctl stop digifor-v2     # Stop service"
echo "  sudo systemctl restart digifor-v2  # Restart service"
echo "  sudo systemctl status digifor-v2    # Cek status service"
echo "  sudo journalctl -u digifor-v2 -f   # Lihat logs"
echo ""
echo "Untuk memulai service sekarang, jalankan:"
echo "  sudo systemctl start digifor-v2"
echo ""

