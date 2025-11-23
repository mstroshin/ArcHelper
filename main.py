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
from src.settings_manager import SettingsManager
from src.settings_gui import SettingsGUI
from src.localization import UI_TEXTS, get_text


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
        self.settings_manager = None
        self.settings_gui = None

    def on_settings_saved(self):
        """Callback when settings are saved."""
        flush_print("\n✓ Settings saved!")
        flush_print("Settings will be applied on next restart.")

    def on_settings_closed(self):
        """Callback when settings window is closed."""
        flush_print("\nSettings window closed. Exiting application...")
        # Stop the application
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        # Exit the program
        import sys
        sys.exit(0)

    def initialize(self):
        """Initialize all components."""
        flush_print("\n" + "=" * 60)
        flush_print("ArcHelperPy - Initializing...")
        flush_print("=" * 60 + "\n")

        # Load settings
        flush_print("Loading settings...")
        self.settings_manager = SettingsManager()
        flush_print(f"✓ Settings loaded (Language: {self.settings_manager.get_language()}, "
                   f"Hotkey: {self.settings_manager.get_recognition_hotkey()})")

        # Check admin privileges
        flush_print("\nChecking administrator privileges...")
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

        # Initialize screen capture with settings
        flush_print("\nInitializing screen capture...")
        capture_size = self.settings_manager.get_capture_size()
        self.screen_capture = ScreenCapture()
        flush_print(f"✓ Screen capture ready (Size: {capture_size[0]}x{capture_size[1]})")

        # Initialize overlay UI with language from settings
        flush_print("\nInitializing overlay UI...")
        self.overlay = OverlayUI(self.database, language=self.settings_manager.get_language())
        flush_print(f"✓ Overlay UI ready (Language: {self.settings_manager.get_language()})")

        # Setup hotkey manager
        flush_print("\nSetting up hotkey manager...")
        self.hotkey_manager = HotkeyManager()

        # Register recognition hotkey from settings
        recognition_hotkey = self.settings_manager.get_recognition_hotkey()
        flush_print(f"\nRegistering recognition hotkey: '{recognition_hotkey}'")

        # Create a wrapper to test callback
        def hotkey_wrapper():
            flush_print(f"\n[DEBUG] Hotkey callback invoked for: {recognition_hotkey}")
            self.on_hotkey_pressed()

        self.hotkey_manager.register_hotkey(recognition_hotkey, hotkey_wrapper)
        flush_print(f"Active hotkey: {recognition_hotkey.upper()}")

        # Test if keyboard library is working
        import keyboard
        flush_print(f"\nKeyboard library version: {keyboard.__version__ if hasattr(keyboard, '__version__') else 'unknown'}")
        flush_print(f"Registered hotkeys in manager: {self.hotkey_manager.registered_hotkeys}")

        flush_print("\n" + "=" * 60)
        flush_print("✓ Initialization complete!")
        flush_print("=" * 60)
        flush_print("\n📋 Usage:")
        flush_print("  1. Hover your cursor over an item in-game")
        flush_print(f"  2. Press {recognition_hotkey.upper()} to identify the item")
        flush_print("  3. View item information in the overlay")
        flush_print("  4. Press ESC or click to close the overlay")
        flush_print("\n⚙️  Settings:")
        flush_print("  - Settings window is open")
        flush_print("  - Close settings window to exit the application")
        flush_print("\nPress Ctrl+C to exit the application\n")

        # Show settings window (non-blocking)
        flush_print("Opening settings window...")
        self.settings_gui = SettingsGUI(self.settings_manager, self.on_settings_saved)
        self.settings_gui.on_close_callback = self.on_settings_closed
        self.settings_gui.show(blocking=False)

    def on_hotkey_pressed(self):
        """Callback when hotkey is pressed."""
        import threading
        import cv2
        from datetime import datetime

        print(f"\n{'='*60}")
        print(f"[HOTKEY] Recognition hotkey triggered!")
        print(f"{'='*60}")

        # Immediately show loading overlay
        try:
            self.overlay.show_loading()
        except Exception:
            pass

        def process_in_thread():
            try:
                print("[INFO] Hotkey pressed, capturing...")

                # Capture screen region under mouse cursor with configured size
                capture_size = self.settings_manager.get_capture_size()
                image = self.screen_capture.capture_at_cursor(size=capture_size)

                if image is None:
                    print("[WARN] Failed to capture image")
                    self._show_not_recognized()
                    return

                # Save screenshot to Debug folder
                debug_dir = Path(__file__).parent / "Debug"
                debug_dir.mkdir(exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = debug_dir / f"capture_{timestamp}.png"
                cv2.imwrite(str(screenshot_path), image)
                print(f"[DEBUG] Screenshot saved to: {screenshot_path}")

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
                    self._show_not_recognized()

            except Exception as e:
                print(f"[ERROR] Error processing hotkey: {e}")
                import traceback
                traceback.print_exc()

        # Run in a separate thread to avoid blocking the hotkey listener
        thread = threading.Thread(target=process_in_thread, daemon=True)
        thread.start()

    def _show_not_recognized(self):
        """Display an overlay indicating the item was not recognized using localization."""
        # Build names for all supported languages
        names = {}
        for lang in UI_TEXTS.keys():
            names[lang] = get_text(lang, 'not_recognized')
        nf = {
            'id': 'not_found',
            'name': names,
            'rarity': 'common'
        }
        try:
            self.overlay.show(nf, duration=6)
        except Exception:
            pass

    def run(self):
        """Start the application."""
        try:
            # Initialize the application (including settings window)
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
        if self.settings_gui:
            self.settings_gui.cleanup()
        print("Goodbye!")


def main():
    """Entry point."""
    app = ArcHelper()
    app.run()


if __name__ == "__main__":
    main()
