#!/bin/bash

# Ensure environment variables are set for SSH sessions
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
sudo loginctl enable-linger $USER

# Define paths relative to HOME
CONFIG_DIR="$HOME/.config/pipewire"
SERVICE_DIR="$HOME/.config/systemd/user"
SCRIPT_PATH="$CONFIG_DIR/virtual-audio.sh"
SERVICE_PATH="$SERVICE_DIR/pipewire-virtual-audio.service"

# Create directories if they don't exist
mkdir -p "$CONFIG_DIR"
mkdir -p "$SERVICE_DIR"

echo "Creating virtual audio script at $SCRIPT_PATH..."

# Create the virtual audio script
cat << 'EOF' > "$SCRIPT_PATH"
#!/bin/bash

# Required for SSH/systemd sessions
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

# Wait for PipeWire to be ready
for i in {1..10}; do
    if pactl info &> /dev/null; then
        break
    fi
    echo "Waiting for PipeWire/PulseAudio server..."
    sleep 1
done

# virtual_sink and its monitor
if ! pactl list short sinks | grep -q "virtual_sink"; then
    pactl load-module module-null-sink sink_name=virtual_sink sink_properties=device.description="Virtual Sink"
fi

# mic_sink and its monitor
if ! pactl list short sinks | grep -q "mic_sink"; then
    pactl load-module module-null-sink sink_name=mic_sink sink_properties=device.description="Mic Sink"
fi

# virtual_mic remapped from virtual_sink.monitor
if ! pactl list short sources | grep -q "virtual_mic"; then
    pactl load-module module-remap-source source_name=virtual_mic master=virtual_sink.monitor
fi

# virtual_mic_2 remapped from mic_sink.monitor
if ! pactl list short sources | grep -q "virtual_mic_2"; then
    pactl load-module module-remap-source source_name=virtual_mic_2 master=mic_sink.monitor
fi
EOF

# Make the script executable
chmod +x "$SCRIPT_PATH"

echo "Creating systemd service at $SERVICE_PATH..."

# Create the systemd user service
# Using %h for home directory in systemd service file for portability
cat << EOF > "$SERVICE_PATH"
[Unit]
Description=Load virtual audio devices for PipeWire
After=pipewire.service
Requires=pipewire.service

[Service]
Type=oneshot
ExecStart=%h/.config/pipewire/virtual-audio.sh
RemainAfterExit=true

[Install]
WantedBy=default.target
EOF

# Reload systemd and enable service
echo "Enabling and starting the service..."
systemctl --user daemon-reload
systemctl --user enable --now pipewire-virtual-audio.service

echo "Done! Virtual audio devices have been configured and started."
pactl list short sinks | grep _sink
pactl list short sources | grep _mic
