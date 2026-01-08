#!/bin/bash
set -e

echo "=== Cloudflared + PipeWire bootstrap starting ==="

########################################
# 1. Install cloudflared if missing
########################################
if ! command -v cloudflared &> /dev/null; then
  echo "[*] Installing cloudflared..."
  curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
  chmod +x /tmp/cloudflared
  sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
else
  echo "[✓] cloudflared already installed"
fi

cloudflared --version

########################################
# 2. Install required audio packages
########################################
echo "[*] Installing PipeWire dependencies..."
sudo apt update
sudo apt install -y \
  pipewire \
  pipewire-pulse \
  wireplumber \
  pipewire-audio-client-libraries \
  pulseaudio-utils

########################################
# 3. Remove legacy PipeWire session manager
########################################
echo "[*] Removing legacy PipeWire session manager (if present)..."
sudo apt remove -y pipewire-media-session || true

########################################
# 4. Disable and mask PulseAudio (user-level)
########################################
echo "[*] Disabling PulseAudio..."
systemctl --user stop pulseaudio.service pulseaudio.socket || true
systemctl --user disable pulseaudio.service pulseaudio.socket || true
systemctl --user mask pulseaudio.service pulseaudio.socket || true

########################################
# 5. Unmask PipeWire stack (common Ubuntu issue)
########################################
echo "[*] Unmasking PipeWire services and sockets..."
systemctl --user unmask pipewire.service pipewire.socket || true
systemctl --user unmask pipewire-pulse.service pipewire-pulse.socket || true
systemctl --user unmask wireplumber.service || true

########################################
# 6. Enable PipeWire stack
########################################
echo "[*] Enabling PipeWire services..."
systemctl --user enable pipewire pipewire.socket
systemctl --user enable pipewire-pulse pipewire-pulse.socket
systemctl --user enable wireplumber

########################################
# 7. Start PipeWire stack
########################################
echo "[*] Starting PipeWire services..."
systemctl --user start pipewire.socket
systemctl --user start pipewire
systemctl --user start pipewire-pulse
systemctl --user start wireplumber

########################################
# 8. Cleanup stale user configs (safe)
########################################
echo "[*] Cleaning stale audio configs..."
rm -rf ~/.config/pulse ~/.pulse || true
rm -rf ~/.local/state/pipewire || true

########################################
# 9. Reload systemd user session
########################################
echo "[*] Reloading systemd user session..."
systemctl --user daemon-reexec

########################################
# 10. Final verification
########################################
echo "[*] Verifying audio server..."
pactl info | grep "Server Name" || true

echo "=== Bootstrap complete ==="
echo "NOTE: If this is the first run, log out and log back in once."
