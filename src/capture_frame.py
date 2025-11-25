"""Capture frame overlay to show screen capture area before capturing."""

import tkinter as tk
import time
from typing import Optional
from src.config import CAPTURE_FRAME_THICKNESS


class CaptureFrame:
    """Shows a flashing frame overlay to indicate screen capture area."""

    def __init__(self):
        """Initialize capture frame."""
        self.window: Optional[tk.Toplevel] = None
        self.is_showing = False

    def show(self, x: int, y: int, width: int, height: int, duration: float = 0.5, auto_hide: bool = True):
        """
        Show a flashing frame at the specified position.

        Args:
            x: Center X coordinate
            y: Center Y coordinate
            width: Frame width
            height: Frame height
            duration: How long to show the frame in seconds (default: 0.5)
            auto_hide: Automatically hide after duration (default: True)
        """
        # Calculate top-left corner (centered on x, y)
        left = x - width // 2
        top = y - height // 2

        # Create window in main thread
        self._create_window(left, top, width, height)

        # Schedule auto-close after duration if requested
        if auto_hide and self.window:
            self.window.after(int(duration * 1000), self.hide)

    def _create_window(self, left: int, top: int, width: int, height: int):
        """Create the frame window."""
        try:
            # Create toplevel window
            self.window = tk.Toplevel()
            self.window.title("Capture Frame")

            # Make it borderless and always on top
            self.window.overrideredirect(True)
            self.window.attributes('-topmost', True)

            # Make window transparent (background)
            self.window.attributes('-transparentcolor', 'black')
            self.window.configure(bg='black')

            # Set window size and position
            self.window.geometry(f"{width}x{height}+{left}+{top}")

            # Create frame border (bright yellow/green for visibility)
            frame_thickness = CAPTURE_FRAME_THICKNESS

            # Top border
            top_bar = tk.Frame(self.window, bg='#00FF00', height=frame_thickness)
            top_bar.pack(side=tk.TOP, fill=tk.X)

            # Bottom border
            bottom_bar = tk.Frame(self.window, bg='#00FF00', height=frame_thickness)
            bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

            # Left border
            left_bar = tk.Frame(self.window, bg='#00FF00', width=frame_thickness)
            left_bar.pack(side=tk.LEFT, fill=tk.Y)

            # Right border
            right_bar = tk.Frame(self.window, bg='#00FF00', width=frame_thickness)
            right_bar.pack(side=tk.RIGHT, fill=tk.Y)

            # Center area (transparent black - will be transparent)
            center = tk.Frame(self.window, bg='black')
            center.pack(expand=True, fill=tk.BOTH)

            # Make sure window is visible
            self.window.update_idletasks()
            self.is_showing = True

            # Start flashing animation
            self._flash_animation(0)

        except Exception as e:
            print(f"[ERROR] Failed to create capture frame: {e}")
            self.window = None

    def _flash_animation(self, count: int):
        """Animate the frame with flashing effect."""
        if not self.window or not self.is_showing:
            return

        try:
            # Alternate between bright green and yellow
            colors = ['#00FF00', '#FFFF00']
            color = colors[count % len(colors)]

            # Update all borders
            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Frame) and widget.cget('bg') != 'black':
                    widget.configure(bg=color)

            # Schedule next flash (10 times per second = smooth animation)
            if count < 5:  # Flash 5 times during 0.5 seconds
                self.window.after(100, lambda: self._flash_animation(count + 1))

        except Exception as e:
            print(f"[ERROR] Flash animation error: {e}")

    def hide(self):
        """Hide and destroy the frame window."""
        self.is_showing = False
        if self.window:
            try:
                self.window.destroy()
            except Exception as e:
                print(f"[ERROR] Failed to destroy capture frame: {e}")
            finally:
                self.window = None

    def cleanup(self):
        """Cleanup resources."""
        self.hide()


def test_capture_frame():
    """Test the capture frame display."""
    print("Testing capture frame...")

    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()

    # Get cursor position (center of screen for testing)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = screen_width // 2
    y = screen_height // 2

    # Create and show frame
    frame = CaptureFrame()
    frame.show(x, y, 160, 160, duration=2.0)  # Show for 2 seconds for testing

    print(f"Frame shown at ({x}, {y}) with size 160x160")
    print("Frame will disappear after 2 seconds...")

    # Keep window alive for duration
    root.after(2500, root.quit)
    root.mainloop()

    frame.cleanup()
    print("Test complete!")


if __name__ == "__main__":
    test_capture_frame()
