#!/bin/bash
# Script untuk mendapatkan token dan menyimpan ke variable

API_URL="${1:-http://172.15.2.160:8000}"
EMAIL="${2:-admin@gmail.com}"
PASSWORD="${3:-admin.admin}"

echo "Logging in to $API_URL..."
echo "Email: $EMAIL"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Login failed!"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "Login successful!"
echo ""
echo "Token:"
echo "$TOKEN"
echo ""
echo "Use in curl:"
echo "Authorization: Bearer $TOKEN"
echo ""
echo "Or export as variable:"
echo "export TOKEN=\"$TOKEN\""
echo "curl -H \"Authorization: Bearer \$TOKEN\" ..."

