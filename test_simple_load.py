"""Simple test to check if settings are loaded correctly."""

from pathlib import Path
from src.settings_manager import SettingsManager

print("Testing SettingsManager...\n")

# Create settings manager
sm = SettingsManager()

print(f"Settings file path: {sm.settings_file}")
print(f"File exists: {sm.settings_file.exists()}")

print(f"\nCurrent settings:")
print(f"  language: {sm.settings.get('language')}")
print(f"  capture_size: {sm.settings.get('capture_size')}")
print(f"  recognition_hotkey: {sm.settings.get('recognition_hotkey')}")

print(f"\nGetter methods:")
print(f"  get_language(): {sm.get_language()}")
print(f"  get_capture_size(): {sm.get_capture_size()}")
print(f"  get_recognition_hotkey(): {sm.get_recognition_hotkey()}")

# Read the file directly
print(f"\nDirect file read:")
if sm.settings_file.exists():
    import json
    with open(sm.settings_file, 'r', encoding='utf-8') as f:
        content = json.load(f)
    print(f"  {content}")
else:
    print("  File not found!")
