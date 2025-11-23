"""
ArcHelperPy - Game Overlay Assistant for Ark Raiders

Main entry point for the application.
Coordinates all components: data loading, hotkey detection, screen capture,
image recognition, and overlay display.
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows console and disable buffering
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from src.data_loader import ItemDatabase
from src.hotkey_manager import HotkeyManager
from src.screen_capture import ScreenCapture
from src.image_recognition import ItemRecognizer
from src.overlay import OverlayUI


def flush_print(*args, **kwargs):
    """Print with immediate flush to ensure output appears in console."""
    print(*args, **kwargs)
    sys.stdout.flush()


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
        flush_print("\n" + "=" * 60)
        flush_print("ArcHelperPy - Initializing...")
        flush_print("=" * 60 + "\n")

        # Check admin privileges
        flush_print("Checking administrator privileges...")
        temp_hotkey = HotkeyManager()
        temp_hotkey.check_admin_privileges()
        temp_hotkey.cleanup()

        # Load item database
        flush_print("\nLoading item database...")
        self.database = ItemDatabase(self.data_dir)
        self.database.load_all_items()
        flush_print(f"✓ Loaded {len(self.database.items)} items")

        # Initialize image recognizer
        flush_print("\nLoading item icons for recognition...")
        self.recognizer = ItemRecognizer(self.data_dir, self.database)
        self.recognizer.load_templates()
        flush_print(f"✓ Loaded {len(self.recognizer.templates)} icon templates")

        # Initialize screen capture
        flush_print("\nInitializing screen capture...")
        self.screen_capture = ScreenCapture()
        flush_print("✓ Screen capture ready")

        # Initialize overlay UI
        flush_print("\nInitializing overlay UI...")
        self.overlay = OverlayUI(self.database)
        flush_print("✓ Overlay UI ready")

        # Setup hotkey manager
        flush_print("\nSetting up hotkey manager...")
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.register_hotkey('ctrl+shift+i', self.on_hotkey_pressed)
        flush_print("✓ Hotkey registered")

        flush_print("\n" + "=" * 60)
        flush_print("✓ Initialization complete!")
        flush_print("=" * 60)
        flush_print("\n📋 Usage:")
        flush_print("  1. Hover your cursor over an item in-game")
        flush_print("  2. Press Ctrl+Shift+I to identify the item")
        flush_print("  3. View item information in the overlay")
        flush_print("  4. Press ESC or click to close the overlay")
        flush_print("\nPress Ctrl+C to exit the application\n")

    def on_hotkey_pressed(self):
        """Callback when hotkey is pressed."""
        import threading

        def process_in_thread():
            try:
                print("[INFO] Hotkey pressed, capturing...")

                # Capture screen region under mouse cursor
                image = self.screen_capture.capture_at_cursor()

                if image is None:
                    print("[WARN] Failed to capture image")
                    return

                print("[INFO] Recognizing item...")

                # Recognize item
                result = self.recognizer.recognize_with_score(image)

                if result:
                    item_id, score = result
                    # Get item data
                    item_data = self.database.get_item(item_id)

                    if item_data:
                        print(f"[INFO] Recognized: {item_data['name']['en']} (confidence: {score:.2%})")

                        # Show overlay with item information (runs in thread to avoid blocking)
                        self.overlay.show(item_data, duration=10)
                    else:
                        print(f"[WARN] Item data not found for ID: {item_id}")
                else:
                    print("[WARN] No item recognized (low confidence)")

                    # Optionally show top matches for debugging
                    top_matches = self.recognizer.get_top_matches(image, 3)
                    if top_matches:
                        print("  Top matches:")
                        for match_id, match_score in top_matches:
                            match_item = self.database.get_item(match_id)
                            match_name = match_item['name']['en'] if match_item else match_id
                            print(f"    - {match_name}: {match_score:.2%}")

            except Exception as e:
                print(f"[ERROR] Error processing hotkey: {e}")
                import traceback
                traceback.print_exc()

        # Run in a separate thread to avoid blocking the hotkey listener
        thread = threading.Thread(target=process_in_thread, daemon=True)
        thread.start()

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
