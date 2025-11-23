"""
ArcHelperPy - Game Overlay Assistant for Ark Raiders

Main entry point for the application.
Coordinates all components: data loading, hotkey detection, screen capture,
image recognition, and overlay display.
"""

import sys
from pathlib import Path

from src.data_loader import ItemDatabase
from src.hotkey_manager import HotkeyManager
from src.screen_capture import ScreenCapture
from src.image_recognition import ItemRecognizer
from src.overlay import OverlayUI


class ArcHelper:
    """Main application class coordinating all components."""

    def __init__(self):
        self.data_dir = Path(__file__).parent / "Data"
        self.database = None
        self.recognizer = None
        self.screen_capture = None
        self.overlay = None
        self.hotkey_manager = None

    def initialize(self):
        """Initialize all components."""
        print("Initializing ArcHelperPy...")

        # Load item database
        print("Loading item database...")
        self.database = ItemDatabase(self.data_dir)
        self.database.load_all_items()
        print(f"Loaded {len(self.database.items)} items")

        # Initialize image recognizer
        print("Loading item icons for recognition...")
        self.recognizer = ItemRecognizer(self.data_dir, self.database)
        self.recognizer.load_templates()
        print(f"Loaded {len(self.recognizer.templates)} icon templates")

        # Initialize screen capture
        self.screen_capture = ScreenCapture()

        # Initialize overlay UI
        self.overlay = OverlayUI(self.database)

        # Setup hotkey manager
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.register_hotkey('ctrl+shift+i', self.on_hotkey_pressed)

        print("Initialization complete!")
        print("Press Ctrl+Shift+I over an item to view its information")
        print("Press Ctrl+C to exit\n")

    def on_hotkey_pressed(self):
        """Callback when hotkey is pressed."""
        try:
            # Capture screen region under mouse cursor
            image = self.screen_capture.capture_at_cursor()

            if image is None:
                return

            # Recognize item
            item_id = self.recognizer.recognize(image)

            if item_id:
                # Get item data
                item_data = self.database.get_item(item_id)

                # Show overlay with item information
                self.overlay.show(item_data)
            else:
                print("No item recognized")

        except Exception as e:
            print(f"Error processing hotkey: {e}")

    def run(self):
        """Start the application."""
        try:
            self.initialize()

            # Keep the application running
            self.hotkey_manager.wait()

        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources."""
        if self.hotkey_manager:
            self.hotkey_manager.cleanup()
        if self.overlay:
            self.overlay.cleanup()
        print("Goodbye!")


def main():
    """Entry point."""
    app = ArcHelper()
    app.run()


if __name__ == "__main__":
    main()
