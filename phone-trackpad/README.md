# 📱 Phone Trackpad

A Proof of Concept (POC) that transforms your phone into a wireless trackpad for your computer using FastAPI and WebSockets.

## 🚀 Features

- **Mouse Movement**: Move your finger on the trackpad to control the cursor
- **Click Controls**: Left and right click buttons
- **Two-finger Scrolling**: Scroll up/down and left/right with two fingers
- **Drag & Drop**: Long press and drag to select and move items
- **Sensitivity Control**: Adjustable cursor sensitivity
- **Real-time WebSocket Communication**: Low-latency mouse control
- **Responsive Design**: Works on all mobile devices
- **Visual Feedback**: Touch indicators and status updates

## 📋 Requirements

- Python 3.8+
- Linux/Windows/macOS
- Phone with a modern web browser
- Both devices on the same network

## 🛠️ Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /home/web-h-063/Documents/virtual-audio-devices/phone-trackpad
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **On Linux, you might need additional system packages:**
   ```bash
   sudo apt-get update
   sudo apt-get install python3-tk python3-dev
   sudo apt-get install scrot python3-pil python3-pil.imagetk
   sudo apt-get install python3-xlib  # For X11 support
   ```

4. **On macOS, you might need:**
   ```bash
   # Grant accessibility permissions to your terminal/Python
   # Go to System Preferences > Security & Privacy > Accessibility
   # Add your terminal application
   ```

5. **On Windows, PyAutoGUI should work out of the box with the pip installation.**

## 🏃‍♂️ Running the Application

1. **Start the server:**
   ```bash
   python main.py
   ```

2. **The server will start on port 8080. You'll see:**
   ```
   Starting Phone Trackpad Server...
   Open http://localhost:8080 on your phone to use as trackpad
   INFO:     Started server process
   INFO:     Uvicorn running on http://0.0.0.0:8080
   ```

3. **Find your computer's IP address:**
   ```bash
   # On Linux/macOS:
   ip addr show | grep "inet " | grep -v 127.0.0.1
   # or
   hostname -I
   
   # On Windows:
   ipconfig | findstr "IPv4"
   ```

4. **Open your phone's web browser and go to:**
   ```
   http://YOUR_COMPUTER_IP:8080
   ```
   (Replace YOUR_COMPUTER_IP with your actual IP address, e.g., http://192.168.1.100:8080)

## 🎮 How to Use

### Basic Controls
- **Move Cursor**: Slide one finger on the trackpad area
- **Left Click**: Tap the "Left Click" button
- **Right Click**: Tap the "Right Click" button
- **Scroll**: Use two fingers and move up/down or left/right
- **Drag & Drop**: Long press (0.5s) on the trackpad, then move your finger while keeping it pressed

### Settings
- **Sensitivity**: Adjust the slider at the bottom to control cursor movement speed
- **Real-time Status**: Connection status is shown in the top-right corner

### Visual Indicators
- **Green dot**: Connected and ready
- **Orange/Red dot**: Disconnected or connecting
- **Touch circles**: Show where your fingers are touching
- **Color change**: Trackpad changes color during drag operations

## 🔧 Configuration

You can modify the following settings in `main.py`:

- **Port**: Change the port number (default: 8080)
- **Sensitivity**: Default sensitivity multiplier (default: 2.0)
- **Long press delay**: Time to trigger drag mode (default: 500ms)

## 🐛 Troubleshooting

### Common Issues

1. **PyAutoGUI import error**:
   ```bash
   pip install pyautogui
   # On Linux, also install system dependencies as mentioned above
   ```

2. **Permission denied on macOS**:
   - Go to System Preferences > Security & Privacy > Accessibility
   - Add Terminal.app or your Python executable to the allowed apps

3. **Connection refused**:
   - Make sure both devices are on the same network
   - Check your firewall settings
   - Verify the IP address is correct

4. **Mouse not moving**:
   - Check if PyAutoGUI is properly installed
   - On Linux, make sure you have X11 forwarding if using SSH
   - Try running with `sudo` if necessary (not recommended for regular use)

5. **Slow response**:
   - Check your network connection
   - Reduce sensitivity if movements are too large
   - Close other network-intensive applications

### Debug Mode

Add this to see more detailed logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Notes

- This application runs a web server that accepts connections from any device on your network
- Only run on trusted networks
- Consider adding authentication for production use
- The server binds to all interfaces (0.0.0.0) for convenience

## 🚀 Future Enhancements

- [ ] Multi-touch gesture support
- [ ] Keyboard input from phone
- [ ] Authentication/security
- [ ] Custom gesture mapping
- [ ] Desktop application with system tray
- [ ] Cross-platform compatibility improvements
- [ ] Mobile app instead of web interface

## 📝 Technical Details

- **Backend**: FastAPI with WebSocket support
- **Frontend**: Vanilla JavaScript with modern touch APIs
- **Mouse Control**: PyAutoGUI for cross-platform mouse automation
- **Communication**: Real-time WebSocket for low latency
- **UI**: Responsive CSS with mobile-first design

## 🤝 Contributing

This is a POC project. Feel free to fork, modify, and improve upon it!

## 📄 License

This project is provided as-is for educational and demonstration purposes.
