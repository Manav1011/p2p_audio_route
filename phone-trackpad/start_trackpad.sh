#!/bin/bash

# Phone Trackpad Launcher Script

echo "🚀 Starting Phone Trackpad Server..."
echo "=============================================="

# Get the computer's IP address
if command -v hostname &> /dev/null; then
    IP=$(hostname -I | awk '{print $1}')
elif command -v ip &> /dev/null; then
    IP=$(ip route get 1 | awk '{print $7}' | head -n1)
else
    IP="localhost"
fi

echo "📱 Computer IP: $IP"
echo "🌐 Open this URL on your phone:"
echo "   http://$IP:8030"
echo ""
echo "🎯 Instructions:"
echo "   1. Make sure your phone is on the same WiFi network"
echo "   2. Open the URL above in your phone's web browser"
echo "   3. Use your phone as a trackpad!"
echo ""
echo "⏹️  Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

# Run the Python server
cd "$(dirname "$0")"
python main.py
