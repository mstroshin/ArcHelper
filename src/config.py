"""Configuration settings for ArcHelperPy."""

# Hotkey configuration
DEFAULT_HOTKEY = 'ctrl+shift+i'  # Hotkey to trigger item recognition

# Image recognition settings
ICON_SIZE = (160, 160)  # Expected size of item icons
MATCH_THRESHOLD = 0.4  # Similarity threshold for image matching (0.0-1.0)

# Screen capture settings
CAPTURE_SIZE = (160, 160)  # Size of the region to capture around cursor

# Overlay settings
OVERLAY_WIDTH = 420
OVERLAY_HEIGHT = 650
OVERLAY_ALPHA = 0.97  # Transparency (0.0-1.0, 1.0 = opaque)

# Language settings
DEFAULT_LANGUAGE = 'en'  # Default language for item names/descriptions

# Supported languages
SUPPORTED_LANGUAGES = [
    'en', 'de', 'fr', 'es', 'pt', 'pl', 'no', 'da',
    'it', 'ru', 'ja', 'zh-TW', 'uk', 'zh-CN', 'kr', 'tr', 'hr', 'sr'
]
