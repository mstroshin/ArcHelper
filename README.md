# ArcHelperPy

A game overlay assistant for Ark Raiders that helps players identify items and understand their crafting recipes and recycling components.

## Features

- **Item Recognition**: Hover over any item in-game and press the hotkey to identify it
- **Crafting Information**: See what materials are needed to craft an item
- **Recycling Details**: View what materials you get from recycling or salvaging items
- **Material Usage**: Find out what items can be crafted using a specific material
- **Multi-language Support**: 22 languages supported
 - **Error Overlay**: Missing item data (e.g. `agave_juice`) now triggers a post-loader error window.

## Requirements

- Python 3.13
- Windows OS

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   py -m pip install -r requirements.txt
   ```

## Usage

### Quick Start

1. **Run as Administrator** (recommended for global hotkeys):

   **Опция А - Использовать bat файл (рекомендуется):**
   ```bash
   # Right-click run.bat → Run as Administrator
   run.bat
   ```

   **Опция Б - Запуск через командную строку:**
   ```bash
   # Right-click Command Prompt → Run as Administrator
   # Используйте один из этих вариантов:
   python -u main.py
   # ИЛИ
   set PYTHONUNBUFFERED=1 && python main.py
   ```

   **Важно:** Флаг `-u` или переменная `PYTHONUNBUFFERED=1` необходимы для немедленного отображения вывода в консоли.

2. The application will initialize:
   - Load 448 items from database
   - Load 270 item icon templates
   - Set up global hotkey listener
   - Display ready message

3. In-game usage:
   - Hover your mouse over an item
   - Press `Ctrl+Shift+I`
   - View item information in the overlay
   - Press `ESC` or click to close

4. Exit the application:
   - Press `Ctrl+C` in the console

### Configuration

Edit `src/config.py` to customize:
- `DEFAULT_HOTKEY`: Change the hotkey (default: `ctrl+shift+i`)
- `CAPTURE_SIZE`: Region size to capture (default: 200x200)
- `MATCH_THRESHOLD`: Recognition confidence (default: 0.8)
- `DEFAULT_LANGUAGE`: Display language (default: `en`)
- `OVERLAY_WIDTH/HEIGHT`: Overlay window size

### Testing

Run individual component tests:
```bash
py test_data_loader.py       # Test item database loading
py test_image_recognition.py # Test image recognition
py test_overlay.py           # Test overlay display
py test_simple.py            # Interactive item query tool
```

See [TESTING.md](TESTING.md) for comprehensive testing guide.

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

## How It Works

1. **Data Loading**: Loads 448 item definitions from JSON files
2. **Image Templates**: Loads 270 PNG item icons for recognition
3. **Hotkey Detection**: Listens for `Ctrl+Shift+I` globally
4. **Screen Capture**: Captures 200x200px region at cursor position
5. **Image Recognition**: Compares captured image against 270 templates using OpenCV
6. **Overlay Display**: Shows item information in a semi-transparent window

## Overlay Information Display

The overlay shows:
- **Item Name** (in your configured language)
- **Type & Rarity**
- **Description**
- **Properties** (weight, stack size, value)
- **Crafting Recipe** (materials needed + craft bench)
- **Recycles Into** (materials from recycling)
- **Salvages Into** (materials from salvaging)
- **Used To Craft** (items that use this material)

## Supported Languages

`en`, `de`, `fr`, `es`, `pt`, `pl`, `no`, `da`, `it`, `ru`, `ja`, `zh-TW`, `uk`, `zh-CN`, `kr`, `tr`, `hr`, `sr`

## Troubleshooting

### Console output not appearing until program closes
- **Solution**: Use `python -u main.py` or `run.bat` instead of `py main.py`
- **Reason**: Python buffers console output by default. The `-u` flag disables buffering.
- **Alternative**: Set environment variable `PYTHONUNBUFFERED=1` before running

### Hotkey not working
- Run as Administrator
- Check if another app uses `Ctrl+Shift+I`
- Try different hotkey in `src/config.py`

### No item recognized
- Ensure item icon is fully visible
- Check icon size matches 200x200px
- Lower `MATCH_THRESHOLD` in config
- Check console for top match suggestions

### Overlay doesn't appear
### Item data missing (e.g., agave_juice)
- Console warning `[WARN] Item data not found for ID: agave_juice` now shows an orange error overlay after the loading spinner.
- Check for a JSON file in `Data/Items/` and confirm it contains an `id` matching `agave_juice`.
- If the item is not yet implemented, the warning is expected.
- Check if window appeared off-screen
- Verify tkinter works: `py -c "import tkinter"`
- Look for errors in console

## Performance

Expected performance:
- Initialization: ~5 seconds
- Hotkey to overlay: ~300-400ms
- Screen capture: <10ms
- Image recognition: 100-200ms (270 comparisons)

## Development Status

**Version 0.1.0 - Core Complete**

✅ All core features implemented:
- Data loading and reverse recipe mapping
- Image recognition with OpenCV
- Screen capture at cursor position
- Global hotkey detection
- Overlay UI with comprehensive info display
- Full integration of all components

⚠️ **Pending**: Real-world game testing for anti-cheat compatibility

## Contributing

Issues and pull requests welcome. Please test thoroughly before submitting changes.

## License

This is a community tool for Ark Raiders players. Use at your own risk.

## Disclaimer

This tool uses screen capture and overlay only. It does not modify game files or memory. However, users should:
- Check game terms of service
- Use at their own risk
- Report any anti-cheat issues immediately

The developers are not responsible for any consequences of using this tool.
