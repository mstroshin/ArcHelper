"""Configuration settings for ArcHelperPy."""

import sys

# Debug mode (disabled in frozen/compiled builds, enabled in development)
DEBUG_MODE = not getattr(sys, 'frozen', False)

# Hotkey configuration
DEFAULT_HOTKEY = 'ctrl+d'  # Hotkey to trigger item recognition
HOTKEY_DEBOUNCE_DELAY = 0.5  # Minimum delay between hotkey triggers in seconds (prevents double-trigger)

# Image recognition settings
ICON_SIZE = (160, 160)  # Expected size of item icons
MATCH_THRESHOLD = 0.4  # Similarity threshold for image matching (0.0-1.0)
MATCH_THRESHOLD_LOW = 0.3  # Lower threshold for "possible match" suggestions

# Screen capture settings
CAPTURE_SIZE = (160, 160)  # Size of the region to capture around cursor
CAPTURE_FRAME_THICKNESS = 4  # Thickness of capture frame border in pixels

# Overlay settings
OVERLAY_WIDTH = 620
OVERLAY_HEIGHT = 650
OVERLAY_ALPHA = 0.97  # Transparency (0.0-1.0, 1.0 = opaque)

# Language settings
DEFAULT_LANGUAGE = 'en'  # Default language for item names/descriptions

# Supported languages
SUPPORTED_LANGUAGES = [
    'en', 'de', 'fr', 'es', 'pt', 'pl', 'no', 'da',
    'it', 'ru', 'ja', 'zh-TW', 'uk', 'zh-CN', 'kr', 'tr', 'hr', 'sr'
]
