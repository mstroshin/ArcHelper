"""Screen capture module for capturing item icons."""

import mss
import numpy as np
import cv2
from typing import Optional
from src.config import CAPTURE_SIZE

try:
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: pywin32 not available, cursor position detection may not work")


class ScreenCapture:
    """Handles screen capture at cursor position."""

    def __init__(self):
        """Initialize screen capture with mss."""
        self.sct = mss.mss()

    def get_cursor_position(self) -> tuple:
        """
        Get the current cursor position.

        Returns:
            Tuple of (x, y) coordinates
        """
        if WIN32_AVAILABLE:
            try:
                point = win32api.GetCursorPos()
                return point
            except Exception as e:
                print(f"Error getting cursor position: {e}")
                return (0, 0)
        else:
            # Fallback: return center of primary monitor
            monitor = self.sct.monitors[1]  # Primary monitor
            return (monitor["width"] // 2, monitor["height"] // 2)

    def capture_at_cursor(self, size: tuple = CAPTURE_SIZE, offset: tuple = (0, 0)) -> Optional[np.ndarray]:
        """
        Capture a region of the screen at the current cursor position.

        Args:
            size: Size of the region to capture (width, height)
            offset: Offset from cursor position (x, y). Default (0, 0) centers on cursor

        Returns:
            Captured image as numpy array (OpenCV format) or None if capture fails
        """
        try:
            # Get cursor position
            cursor_x, cursor_y = self.get_cursor_position()

            # Calculate capture region (centered on cursor + offset)
            width, height = size
            left = cursor_x - width // 2 + offset[0]
            top = cursor_y - height // 2 + offset[1]

            # Define the monitor region to capture
            monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }

            # Capture the screen
            screenshot = self.sct.grab(monitor)

            # Convert to numpy array
            img = np.array(screenshot)

            # Convert from BGRA to BGR (OpenCV format)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            return img

        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None

    def capture_region(self, left: int, top: int, width: int, height: int) -> Optional[np.ndarray]:
        """
        Capture a specific region of the screen.

        Args:
            left: Left coordinate
            top: Top coordinate
            width: Width of region
            height: Height of region

        Returns:
            Captured image as numpy array (OpenCV format) or None if capture fails
        """
        try:
            monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }

            screenshot = self.sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            return img

        except Exception as e:
            print(f"Error capturing region: {e}")
            return None

    def capture_full_screen(self, monitor_number: int = 1) -> Optional[np.ndarray]:
        """
        Capture the full screen of a specific monitor.

        Args:
            monitor_number: Monitor number (1 = primary, 2 = secondary, etc.)

        Returns:
            Captured image as numpy array (OpenCV format) or None if capture fails
        """
        try:
            if monitor_number < 1 or monitor_number > len(self.sct.monitors) - 1:
                print(f"Invalid monitor number: {monitor_number}")
                return None

            monitor = self.sct.monitors[monitor_number]
            screenshot = self.sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            return img

        except Exception as e:
            print(f"Error capturing full screen: {e}")
            return None

    def get_monitor_info(self) -> list:
        """
        Get information about all available monitors.

        Returns:
            List of monitor dictionaries
        """
        return self.sct.monitors

    def cleanup(self):
        """Cleanup screen capture resources."""
        if hasattr(self, 'sct'):
            self.sct.close()
