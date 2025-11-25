"""Hotkey management module for global hotkey detection."""

import keyboard
import threading
import time
from typing import Callable
from src.config import HOTKEY_DEBOUNCE_DELAY


class HotkeyManager:
    """Manages global hotkey detection using the keyboard library."""

    def __init__(self, debounce_delay: float = HOTKEY_DEBOUNCE_DELAY):
        """Initialize the hotkey manager.

        Args:
            debounce_delay: Minimum delay between hotkey triggers in seconds (default from config)
        """
        self.registered_hotkeys = []
        self.running = False
        self._last_trigger_time = {}  # Track last trigger time per hotkey for debouncing
        self._debounce_delay = debounce_delay  # Minimum delay between triggers in seconds
        self._hotkey_pressed = {}  # Track if hotkey is currently being held down

    def register_hotkey(self, hotkey: str, callback: Callable):
        """
        Register a global hotkey with debouncing to prevent double triggers.

        Args:
            hotkey: Hotkey string (e.g., 'ctrl+shift+i')
            callback: Function to call when hotkey is pressed

        Note:
            On Windows, this may require administrator privileges for global hotkey detection.
        """
        try:
            # First, remove any existing registration for this hotkey
            try:
                keyboard.remove_hotkey(hotkey)
            except:
                pass

            # Initialize the pressed state for this hotkey
            self._hotkey_pressed[hotkey] = False

            # Create a wrapper that only triggers once per key press (not while held)
            def single_trigger_callback():
                # Only trigger if this is the first press (not being held)
                if not self._hotkey_pressed.get(hotkey, False):
                    current_time = time.time()
                    last_time = self._last_trigger_time.get(hotkey, 0)

                    # Check if enough time has passed since last trigger
                    if current_time - last_time >= self._debounce_delay:
                        self._hotkey_pressed[hotkey] = True  # Mark as pressed
                        self._last_trigger_time[hotkey] = current_time
                        callback()

                        # Start a thread to wait for key release
                        def wait_for_release():
                            # Wait until all keys in the combination are released
                            keys = hotkey.split('+')
                            while any(keyboard.is_pressed(key) for key in keys):
                                time.sleep(0.01)
                            # Reset the pressed state once released
                            self._hotkey_pressed[hotkey] = False
                            print(f"[DEBUG] Hotkey '{hotkey}' released and ready for next press")

                        threading.Thread(target=wait_for_release, daemon=True).start()
                    else:
                        print(f"[DEBUG] Hotkey '{hotkey}' debounced (too soon: {current_time - last_time:.3f}s)")
                else:
                    # Hotkey is being held down - ignore this trigger
                    pass

            # Register the hotkey with the keyboard library using single-trigger wrapper
            keyboard.add_hotkey(hotkey, single_trigger_callback, suppress=False)
            self.registered_hotkeys.append(hotkey)
            print(f"✓ Registered hotkey: {hotkey} (with {self._debounce_delay}s debounce)")

            # Test if hotkey is actually registered
            if keyboard.is_pressed(hotkey.split('+')[-1]):
                print(f"  (Key '{hotkey.split('+')[-1]}' is currently being pressed)")

        except Exception as e:
            print(f"✗ Error registering hotkey '{hotkey}': {e}")
            print("  Note: Global hotkeys may require administrator privileges on Windows")
            import traceback
            traceback.print_exc()

    def unregister_hotkey(self, hotkey: str):
        """
        Unregister a specific hotkey.

        Args:
            hotkey: Hotkey string to unregister
        """
        try:
            keyboard.remove_hotkey(hotkey)
            if hotkey in self.registered_hotkeys:
                self.registered_hotkeys.remove(hotkey)
            print(f"Unregistered hotkey: {hotkey}")

        except Exception as e:
            print(f"Error unregistering hotkey '{hotkey}': {e}")

    def wait(self):
        """
        Wait for hotkey events. This blocks until cleanup() is called.
        """
        self.running = True
        try:
            # Keep the program running and listening for hotkeys
            while self.running:
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        finally:
            self.running = False

    def stop(self):
        """Stop waiting for hotkey events."""
        self.running = False

    def cleanup(self):
        """Cleanup all registered hotkey handlers."""
        try:
            self.running = False

            # Remove all registered hotkeys
            for hotkey in self.registered_hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey)
                except Exception as e:
                    print(f"Error removing hotkey '{hotkey}': {e}")

            # Clear the list
            self.registered_hotkeys.clear()

            # Clear debounce tracking
            self._last_trigger_time.clear()

            # Clear pressed state tracking
            self._hotkey_pressed.clear()

            # Unhook all keyboard hooks
            keyboard.unhook_all()

            print("Hotkey manager cleaned up")

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def is_admin(self) -> bool:
        """
        Check if the program is running with administrator privileges.

        Returns:
            True if running as admin, False otherwise
        """
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def check_admin_privileges(self):
        """
        Check for admin privileges and warn if not running as admin.
        """
        if not self.is_admin():
            print("\n" + "!" * 60)
            print("WARNING: Not running with administrator privileges!")
            print("Global hotkeys may not work properly.")
            print("Consider running the program as Administrator.")
            print("!" * 60 + "\n")
        else:
            print("Running with administrator privileges ✓")
