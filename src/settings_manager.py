"""Settings manager for ArcHelperPy."""

import json
from pathlib import Path
from typing import Any, Dict
from src.config import (
    DEFAULT_HOTKEY,
    CAPTURE_SIZE,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES
)


class SettingsManager:
    """Manages application settings with persistence."""

    def __init__(self, settings_file: Path = None):
        """
        Initialize settings manager.

        Args:
            settings_file: Path to settings JSON file. Defaults to settings.json in project root.
        """
        if settings_file is None:
            # Default to settings.json in project root
            self.settings_file = Path(__file__).parent.parent / "settings.json"
        else:
            self.settings_file = settings_file

        self.settings = self._load_default_settings()
        self.load()

    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default settings."""
        return {
            "language": DEFAULT_LANGUAGE,
            "capture_size": list(CAPTURE_SIZE),  # [width, height]
            "recognition_hotkey": DEFAULT_HOTKEY,
        }

    def load(self) -> bool:
        """
        Load settings from file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)

                print(f"[DEBUG] Loaded settings from file: {loaded_settings}")

                # Merge with defaults (in case new settings were added)
                self.settings.update(loaded_settings)

                print(f"[DEBUG] Settings after merge: {self.settings}")

                # Validate settings
                self._validate_settings()

                print(f"Settings loaded from {self.settings_file}")
                return True
            else:
                print(f"No settings file found at {self.settings_file}, using defaults")
                print(f"[DEBUG] Default settings: {self.settings}")
                return False

        except Exception as e:
            print(f"Error loading settings: {e}")
            print("Using default settings")
            return False

    def save(self) -> bool:
        """
        Save settings to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure parent directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)

            print(f"Settings saved to {self.settings_file}")
            return True

        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def _validate_settings(self):
        """Validate and fix invalid settings."""
        # Validate language
        if self.settings["language"] not in SUPPORTED_LANGUAGES:
            print(f"Invalid language '{self.settings['language']}', using default")
            self.settings["language"] = DEFAULT_LANGUAGE

        # Validate capture size
        if not isinstance(self.settings["capture_size"], list) or len(self.settings["capture_size"]) != 2:
            print(f"Invalid capture size, using default")
            self.settings["capture_size"] = list(CAPTURE_SIZE)
        else:
            # Ensure values are integers and reasonable
            width, height = self.settings["capture_size"]
            if not (50 <= width <= 500) or not (50 <= height <= 500):
                print(f"Capture size out of range, using default")
                self.settings["capture_size"] = list(CAPTURE_SIZE)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: Setting key
            default: Default value if key doesn't exist

        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value

    def get_language(self) -> str:
        """Get current language setting."""
        return self.settings["language"]

    def set_language(self, language: str):
        """Set language setting."""
        if language in SUPPORTED_LANGUAGES:
            self.settings["language"] = language
        else:
            raise ValueError(f"Unsupported language: {language}")

    def get_capture_size(self) -> tuple:
        """Get capture size as tuple."""
        return tuple(self.settings["capture_size"])

    def set_capture_size(self, width: int, height: int):
        """Set capture size."""
        if 50 <= width <= 500 and 50 <= height <= 500:
            self.settings["capture_size"] = [width, height]
        else:
            raise ValueError(f"Capture size must be between 50 and 500 pixels")

    def get_recognition_hotkey(self) -> str:
        """Get recognition hotkey."""
        return self.settings["recognition_hotkey"]

    def set_recognition_hotkey(self, hotkey: str):
        """Set recognition hotkey."""
        self.settings["recognition_hotkey"] = hotkey

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self._load_default_settings()
