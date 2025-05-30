Here’s the **complete and corrected setup** for creating **virtual audio devices** using PipeWire and PulseAudio compatibility, including installation steps, script, service, and activation.

---

## ✅ Step 1: Install Required Packages

### 📦 For Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y pipewire pipewire-audio-client-libraries pulseaudio-utils
```

> ✅ `pulseaudio-utils` provides `pactl` (still used under PipeWire for compatibility).
> ✅ `pipewire-audio-client-libraries` ensures PulseAudio clients work with PipeWire.

To confirm PipeWire is being used as the audio server:

```bash
pactl info | grep "Server Name"
```

Expected output: `Server Name: PulseAudio (on PipeWire ...)`

---

## ✅ Step 2: Create Virtual Audio Script

File: `~/.config/pipewire/virtual-audio.sh`

```bash
#!/bin/bash

# Load virtual_sink and its monitor
if ! pactl list short sinks | grep -q "virtual_sink"; then
  pactl load-module module-null-sink sink_name=virtual_sink sink_properties=device.description="Virtual Sink"
fi

# Load mic_sink and its monitor
if ! pactl list short sinks | grep -q "mic_sink"; then
  pactl load-module module-null-sink sink_name=mic_sink sink_properties=device.description="Mic Sink"
fi

# Remap virtual_sink.monitor as virtual_mic
if ! pactl list short sources | grep -q "virtual_mic"; then
  pactl load-module module-remap-source source_name=virtual_mic master=virtual_sink.monitor
fi

# Remap mic_sink.monitor as virtual_mic_2
if ! pactl list short sources | grep -q "virtual_mic_2"; then
  pactl load-module module-remap-source source_name=virtual_mic_2 master=mic_sink.monitor
fi
```

Make it executable:

```bash
chmod +x ~/.config/pipewire/virtual-audio.sh
```

---

## ✅ Step 3: Create systemd User Service

File: `~/.config/systemd/user/pipewire-virtual-audio.service`

```ini
[Unit]
Description=Load virtual audio devices for PipeWire
After=pipewire.service
Requires=pipewire.service

[Service]
Type=oneshot
ExecStart=/home/web-h-063/.config/pipewire/virtual-audio.sh
RemainAfterExit=true

[Install]
WantedBy=default.target
```

---

## ✅ Step 4: Enable & Start the Service

```bash
systemctl --user daemon-reexec
systemctl --user daemon-reload
systemctl --user enable --now pipewire-virtual-audio.service
```

If you get permissions errors, ensure you have `systemd` running in user mode and your session is active.

---

## ✅ Step 5: Verify Virtual Devices

Run:

```bash
pactl list short sinks
pactl list short sources
```

You should see:

* `virtual_sink`
* `mic_sink`
* `virtual_mic`
* `virtual_mic_2`

---

## ✅ Troubleshooting

* If it doesn’t auto-start on reboot, ensure **user lingering** is enabled:

  ```bash
  sudo loginctl enable-linger $USER
  ```
* Make sure you're logged in graphically (not just via SSH), as user services depend on an active session.

---

Let me know if you also want a `PipeWire` configuration file to route audio between these virtual devices automatically.
