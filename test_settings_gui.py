"""Test script to check settings GUI initialization."""

from src.settings_manager import SettingsManager
from src.settings_gui import SettingsGUI

# Create settings manager
print("Creating SettingsManager...")
sm = SettingsManager()

print(f"\nSettings loaded:")
print(f"  Language: {sm.get_language()}")
print(f"  Hotkey: {sm.get_recognition_hotkey()}")
print(f"  Capture size: {sm.get_capture_size()}")

print(f"\nRaw settings dict:")
print(f"  {sm.settings}")

# Create and show GUI
print("\nOpening settings GUI...")
gui = SettingsGUI(sm)
gui.show(blocking=True)

print("\nGUI closed.")
print(f"Was cancelled: {gui.was_cancelled()}")

print(f"\nFinal settings:")
print(f"  Language: {sm.get_language()}")
print(f"  Hotkey: {sm.get_recognition_hotkey()}")
print(f"  Capture size: {sm.get_capture_size()}")
