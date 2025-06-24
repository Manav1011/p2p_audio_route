#!/bin/bash

# Go to directory
cd /home/web-h-063/Documents/virtual-audio-devices

# Run Python script
/home/web-h-063/.globalvenv/bin/python /home/web-h-063/Documents/virtual-audio-devices/main.py &

# Run Cloudflare tunnel
cloudflared tunnel --config /home/web-h-063/.cloudflared/p2p_route/config.yml run p2p_route
