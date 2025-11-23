# ArcHelperPy

A game overlay assistant for Ark Raiders that helps players identify items and understand their crafting recipes and recycling components.

## Features

- **Item Recognition**: Hover over any item in-game and press the hotkey to identify it
- **Crafting Information**: See what materials are needed to craft an item
- **Recycling Details**: View what materials you get from recycling or salvaging items
- **Material Usage**: Find out what items can be crafted using a specific material
- **Multi-language Support**: 22 languages supported

## Requirements

- Python 3.13
- Windows OS

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. The application will load all item data and start listening for hotkeys

3. In-game, hover your mouse over an item and press `Ctrl+Shift+I` to view item information

4. Press `Ctrl+C` to exit the application

## Project Structure

```
ArcHelperPy/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── Data/
│   └── Items/              # Item JSON files and icons
│       ├── *.json          # Item metadata (448 files)
│       └── Images/         # Item icon images
└── src/
    ├── config.py           # Configuration settings
    ├── data_loader.py      # Item database loader
    ├── image_recognition.py # Item recognition from images
    ├── screen_capture.py   # Screen capture functionality
    ├── hotkey_manager.py   # Global hotkey detection
    └── overlay.py          # Overlay UI display
```

## Anti-Cheat Safety

This application is designed to be safe and non-intrusive:
- Does NOT hook into game process memory
- Does NOT inject any DLLs
- Only uses screen capture and overlay rendering
- Operates as a completely separate process

## Development Status

This project is currently under development. Core modules are being implemented.
