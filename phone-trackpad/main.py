#!/usr/bin/env python3

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

try:
    import warnings
    # Suppress tkinter warnings
    warnings.filterwarnings("ignore", message=".*tkinter.*")
    warnings.filterwarnings("ignore", message=".*MouseInfo.*")
    
    import pyautogui
    pyautogui.FAILSAFE = False  # Disable fail-safe for smoother operation
    pyautogui.PAUSE = 0.01  # Reduce pause between operations for responsiveness
    
    # Test if PyAutoGUI can get screen size (this will fail if X11 is not available)
    try:
        _ = pyautogui.size()
        print("✅ PyAutoGUI initialized successfully")
    except Exception as e:
        print(f"⚠️  PyAutoGUI initialization warning: {e}")
        print("   Mouse control may not work in headless environments")
        
except ImportError as e:
    print(f"❌ PyAutoGUI import error: {e}")
    print("Install with: pip install pyautogui")
    print("On Linux, you might also need: sudo apt-get install python3-tk python3-dev")
    pyautogui = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Phone Trackpad", description="Use your phone as a trackpad for your computer")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

class TrackpadEvent(BaseModel):
    type: str  # "move", "click", "scroll", "drag_start", "drag_end", "selection_start", "selection_end", "zoom", "gesture"
    x: float = 0
    y: float = 0
    deltaX: float = 0
    deltaY: float = 0
    delta: float = 0  # For zoom events
    button: str = "left"  # "left", "right", "middle"

class MouseController:
    def __init__(self):
        self.is_dragging = False
        self.is_selecting = False
        self.sensitivity = 2.0
        self.screen_width, self.screen_height = pyautogui.size() if pyautogui else (1920, 1080)
        logger.info(f"Screen size: {self.screen_width}x{self.screen_height}")

    def move_mouse(self, delta_x: float, delta_y: float):
        """Move mouse cursor relative to current position"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
        
        try:
            # Apply sensitivity
            move_x = int(delta_x * self.sensitivity)
            move_y = int(delta_y * self.sensitivity)
            
            # Get current position
            current_x, current_y = pyautogui.position()
            
            # Calculate new position with bounds checking
            new_x = max(0, min(self.screen_width - 1, current_x + move_x))
            new_y = max(0, min(self.screen_height - 1, current_y + move_y))
            
            pyautogui.moveTo(new_x, new_y)
            logger.debug(f"Mouse moved to: {new_x}, {new_y}")
            
        except Exception as e:
            logger.error(f"Error moving mouse: {e}")

    def click(self, button: str = "left"):
        """Perform mouse click"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            if button == "right":
                pyautogui.rightClick()
            elif button == "middle":
                pyautogui.middleClick()
            else:
                pyautogui.leftClick()
            logger.debug(f"Mouse {button} click")
            
        except Exception as e:
            logger.error(f"Error clicking mouse: {e}")

    def scroll(self, delta_x: float, delta_y: float):
        """Perform scroll action with both horizontal and vertical support"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            # Convert delta to scroll units (pyautogui uses integer scroll units)
            scroll_y = int(delta_y / 8)  # Adjusted sensitivity for smoother scrolling
            scroll_x = int(delta_x / 8)
            
            # Vertical scrolling
            if scroll_y != 0:
                pyautogui.scroll(scroll_y)
            
            # Horizontal scrolling using keyboard shortcuts
            if scroll_x != 0:
                if scroll_x > 0:
                    # Scroll right - use Shift+Scroll or simulate horizontal scroll
                    for _ in range(abs(scroll_x)):
                        pyautogui.keyDown('shift')
                        pyautogui.scroll(1)
                        pyautogui.keyUp('shift')
                else:
                    # Scroll left
                    for _ in range(abs(scroll_x)):
                        pyautogui.keyDown('shift')
                        pyautogui.scroll(-1)
                        pyautogui.keyUp('shift')
            
            logger.debug(f"Mouse scroll: x={scroll_x}, y={scroll_y}")
            
        except Exception as e:
            logger.error(f"Error scrolling: {e}")

    def drag_start(self):
        """Start drag operation"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            pyautogui.mouseDown()
            self.is_dragging = True
            logger.debug("Drag started")
            
        except Exception as e:
            logger.error(f"Error starting drag: {e}")

    def drag_end(self):
        """End drag operation"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            pyautogui.mouseUp()
            self.is_dragging = False
            logger.debug("Drag ended")
            
        except Exception as e:
            logger.error(f"Error ending drag: {e}")

    def selection_start(self):
        """Start text selection"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            # Double click to select word, then start selection mode
            pyautogui.doubleClick()
            pyautogui.mouseDown()
            self.is_selecting = True
            logger.debug("Text selection started")
            
        except Exception as e:
            logger.error(f"Error starting text selection: {e}")

    def zoom(self, delta: float):
        """Perform zoom action using Ctrl + scroll wheel"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            pyautogui.keyDown('ctrl')
            pyautogui.scroll(int(delta))
            pyautogui.keyUp('ctrl')
            logger.debug(f"Zoom: {delta}")
            
        except Exception as e:
            logger.error(f"Error zooming: {e}")

    def show_desktop(self):
        """Show desktop / minimize all windows"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            # Windows: Win+D, Mac: F11, Linux: Ctrl+Alt+D
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                pyautogui.hotkey('win', 'd')
            elif system == "darwin":  # macOS
                pyautogui.hotkey('f11')
            else:  # Linux
                pyautogui.hotkey('ctrl', 'alt', 'd')
                
            logger.debug("Show desktop gesture executed")
            
        except Exception as e:
            logger.error(f"Error showing desktop: {e}")

    def selection_end(self):
        """End text selection"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            pyautogui.mouseUp()
            self.is_selecting = False
            logger.debug("Text selection ended")
            
        except Exception as e:
            logger.error(f"Error ending text selection: {e}")

    def double_click(self, button: str = "left"):
        """Perform double click"""
        if not pyautogui:
            logger.warning("pyautogui not available")
            return
            
        try:
            if button == "right":
                pyautogui.doubleClick(button='right')
            elif button == "middle":
                pyautogui.doubleClick(button='middle')
            else:
                pyautogui.doubleClick(button='left')
            logger.debug(f"Double {button} click")
            
        except Exception as e:
            logger.error(f"Error double clicking: {e}")

# Global mouse controller instance
mouse_controller = MouseController()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main trackpad interface"""
    return templates.TemplateResponse("trackpad.html", {"request": request})

@app.get("/status")
async def get_status():
    """Get server status"""
    return {
        "status": "running",
        "pyautogui_available": pyautogui is not None,
        "screen_size": {
            "width": mouse_controller.screen_width,
            "height": mouse_controller.screen_height
        },
        "sensitivity": mouse_controller.sensitivity,
        "active_connections": len(active_connections)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time trackpad events"""
    await websocket.accept()
    connection_id = f"conn_{len(active_connections)}"
    active_connections[connection_id] = websocket
    
    logger.info(f"New WebSocket connection: {connection_id}")
    
    try:
        while True:
            # Receive trackpad event
            data = await websocket.receive_text()
            
            try:
                event_data = json.loads(data)
                event = TrackpadEvent(**event_data)
                
                # Process the event
                await process_trackpad_event(event)
                
                # Send acknowledgment
                await websocket.send_text(json.dumps({
                    "type": "ack",
                    "success": True,
                    "event_type": event.type
                }))
                
            except Exception as e:
                logger.error(f"Error processing trackpad event: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]

async def process_trackpad_event(event: TrackpadEvent):
    """Process different types of trackpad events"""
    try:
        if event.type == "move":
            mouse_controller.move_mouse(event.deltaX, event.deltaY)
            
        elif event.type == "click":
            mouse_controller.click(event.button)
            
        elif event.type == "scroll":
            mouse_controller.scroll(event.deltaX, event.deltaY)
            
        elif event.type == "drag_start":
            mouse_controller.drag_start()
            
        elif event.type == "drag_end":
            mouse_controller.drag_end()
            
        elif event.type == "selection_start":
            mouse_controller.selection_start()
            
        elif event.type == "selection_end":
            mouse_controller.selection_end()
            
        elif event.type == "zoom":
            mouse_controller.zoom(event.delta)
            
        elif event.type == "gesture":
            # Handle gesture events (like show desktop)
            if hasattr(event, 'gesture_type') and event.gesture_type == "show_desktop":
                mouse_controller.show_desktop()
            
        else:
            logger.warning(f"Unknown event type: {event.type}")
            
    except Exception as e:
        logger.error(f"Error processing event {event.type}: {e}")
        raise

@app.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update trackpad settings"""
    if "sensitivity" in settings:
        mouse_controller.sensitivity = float(settings["sensitivity"])
        logger.info(f"Sensitivity updated to: {mouse_controller.sensitivity}")
    
    return {
        "success": True,
        "settings": {
            "sensitivity": mouse_controller.sensitivity
        }
    }

if __name__ == "__main__":
    # Check if pyautogui is available
    if pyautogui is None:
        print("\n" + "="*60)
        print("WARNING: pyautogui is not installed!")
        print("Install it with:")
        print("  pip install pyautogui")
        print("\nOn Linux, you might also need:")
        print("  sudo apt-get install python3-tk python3-dev")
        print("  sudo apt-get install scrot python3-pil python3-pil.imagetk")
        print("="*60 + "\n")
    
    print("Starting Phone Trackpad Server...")
    print("Open http://localhost:8030 on your phone to use as trackpad")
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8030,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print("\n=== ERROR STARTING SERVER ===")
        print(str(e))
        import traceback
        traceback.print_exc()
        print("============================\n")
