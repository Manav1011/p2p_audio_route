#!/bin/bash

# Go to directory
cd ~/Documents/virtual-audio-devices

# Run Python script
/home/web-h-063/.globalvenv/bin/python ~/Documents/virtual-audio-devices/main.py &

# Run Cloudflare tunnel
cloudflared tunnel --config ~/.cloudflared/p2p_route/config.yml run p2p_route
