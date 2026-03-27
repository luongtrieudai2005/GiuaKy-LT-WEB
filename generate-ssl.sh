#!/bin/bash
# ============================================================
# generate-ssl.sh — Linux / Mac / Git Bash
# Tạo self-signed SSL certificate cho local development.
#
# Chạy một lần trước khi docker compose up:
#   bash generate-ssl.sh
# ============================================================

set -e

SSL_DIR="./nginx/ssl"
mkdir -p "$SSL_DIR"

echo "Generating self-signed SSL certificate..."

openssl req -x509 \
    -nodes \
    -days 365 \
    -newkey rsa:2048 \
    -keyout "$SSL_DIR/key.pem" \
    -out    "$SSL_DIR/cert.pem" \
    -subj "/C=VN/ST=HCM/L=HoChiMinh/O=TaskManager/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo ""
echo "SSL certificate generated:"
echo "  cert: $SSL_DIR/cert.pem"
echo "  key:  $SSL_DIR/key.pem"
echo ""
echo "Done. Now run: docker compose up --build"