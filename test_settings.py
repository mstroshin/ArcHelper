"""Test script to verify settings manager and GUI."""

from src.settings_manager import SettingsManager
from src.settings_gui import SettingsGUI

def test_settings():
    """Test settings manager."""
    print("Testing Settings Manager...")
    print("-" * 50)

    # Create settings manager
    settings = SettingsManager()

    # Print current settings
    print(f"Language: {settings.get_language()}")
    print(f"Capture Size: {settings.get_capture_size()}")
    print(f"Recognition Hotkey: {settings.get_recognition_hotkey()}")

    print("\n✓ Settings loaded successfully!")
    print("-" * 50)

    # Test GUI
    print("\nOpening Settings GUI...")
    print("Press Ctrl+Shift+S would normally open this window.")

    gui = SettingsGUI(settings)
    gui.show()

if __name__ == "__main__":
    test_settings()
