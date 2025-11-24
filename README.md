# ArcHelperPy

A **production-ready** game overlay assistant for Ark Raiders that helps players identify items and understand their crafting recipes, recycling components, and hideout bench usage.

## Features

- **Advanced Item Recognition**: Multi-method image recognition using 5 different techniques (Template Matching, Histogram Equalization, Color Histograms, ORB & SIFT Features)
- **Comprehensive Item Information**:
  - Crafting recipes with required materials and craft bench
  - Recycling and salvaging output
  - Reverse lookup: What items can be crafted using this material
  - Hideout bench upgrade requirements
- **Interactive Overlay**: Click on materials to open their information in new windows
- **Multi-language Support**: 22 languages supported
- **Customizable Settings**: Adjustable hotkey, capture size, and language
- **Settings GUI**: User-friendly configuration window
- **Safe & Non-Intrusive**: No game memory access, DLL injection, or process hooking

## Requirements

- **Python 3.13+**
- **Windows OS** (requires administrator privileges for global hotkeys)
- **Dependencies**: See [requirements.txt](requirements.txt)

## Installation

### Option A: Use Pre-built Executable (Recommended)

1. Download the latest release from the releases page
2. Extract the ZIP file
3. Run `ArcHelper.exe` as Administrator
4. Configure settings in the Settings window that opens automatically

### Option B: Run from Source

1. Clone or download this repository
2. Install Python 3.13+
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Usage

### Quick Start

1. **Run as Administrator** (required for global hotkeys):
   - **Executable**: Right-click `ArcHelper.exe` → "Run as administrator"
   - **Source**: Right-click Command Prompt → "Run as administrator", then `python main.py`

2. **Configure Settings**:
   - Settings window opens automatically on first run
   - Choose your language (22 available)
   - Set hotkey (default: `Ctrl+D`)
   - Adjust capture size (default: 160x160px)
   - Close settings window to exit (settings are saved automatically)

3. **In-game Usage**:
   - Hover your cursor over an item in-game
   - Press your configured hotkey (default: `Ctrl+D`)
   - View comprehensive item information in the overlay
   - **Click on any material** to open its information in a new window
   - Press `ESC` or click outside to close the overlay

4. **Exit**:
   - Close the settings window, or
   - Press `Ctrl+C` in console (if running from source)

### Settings

**Via Settings GUI** (recommended):
- Open settings window to configure all options
- Changes persist in `settings.json`
- Settings apply on next restart

**Via Configuration File** (`src/config.py`):
- `DEFAULT_HOTKEY`: Default hotkey (default: `ctrl+d`)
- `CAPTURE_SIZE`: Screenshot region size (default: 160x160px)
- `MATCH_THRESHOLD`: Recognition confidence threshold (default: 0.4 = 40%)
- `DEFAULT_LANGUAGE`: Default UI language (default: `en`)
- `OVERLAY_WIDTH/HEIGHT`: Overlay window dimensions
- `HOTKEY_DEBOUNCE_DELAY`: Prevent double-triggers (default: 0.5s)

## Project Structure

```
ArcHelperPy/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── settings.json             # User settings (auto-generated)
├── ArcHelper.spec            # PyInstaller build spec (release)
├── ArcHelperDebug.spec       # PyInstaller build spec (debug)
├── Data/
│   ├── Items/                # 448 item JSON files
│   │   ├── *.json            # Item metadata
│   │   └── Images/           # Item icons (WebP, 160x160px)
│   └── Hideout/              # 9 hideout bench JSON files
├── Debug/                    # Captured screenshots (auto-generated)
└── src/
    ├── config.py             # Configuration constants
    ├── data_loader.py        # ItemDatabase class (items + hideout)
    ├── image_recognition.py  # Multi-method image matching
    ├── screen_capture.py     # DPI-aware screen capture
    ├── hotkey_manager.py     # Global hotkey with debouncing
    ├── overlay.py            # Modern overlay UI system
    ├── settings_manager.py   # Settings persistence
    ├── settings_gui.py       # Settings configuration window
    └── localization.py       # Multi-language UI text (22 languages)
```

## Anti-Cheat Safety

**This application follows strict anti-cheat guidelines:**

✅ **Safe:**
- Uses only screen capture (mss library)
- Renders overlay in separate process
- No game memory access
- No DLL injection or process hooking
- Non-suppressing hotkeys (game receives input)
- No interaction with game files

❌ **Does NOT:**
- Hook into game process
- Read game memory
- Modify game files
- Inject code into the game
- Interfere with anti-cheat systems

**The application is purely passive** - it watches the screen and displays information in a separate window, similar to a second monitor or overlay like Discord/OBS.

## How It Works

### Image Recognition Pipeline

1. **Multi-Method Recognition** (5 techniques combined with weighted scoring):
   - Template Matching (TM_CCOEFF_NORMED) - 25%
   - Correlation Coefficient (TM_CCORR_NORMED) - 15%
   - Histogram-Equalized Matching - 30% (lighting invariant)
   - Color Histogram Comparison - 15%
   - ORB Feature Matching - 15% (rotation/scale invariant, 500 features)
   - **Confidence threshold**: 40% (configurable)

2. **Workflow**:
   - User presses hotkey (`Ctrl+D`)
   - Capture 160x160px region centered on cursor
   - Save debug screenshot to `Debug/` folder
   - Apply multi-method recognition against 448 item templates
   - Display comprehensive item information if match >= 40%

3. **Data Architecture**:
   - **448 items** with JSON metadata + WebP icons (160x160px)
   - **9 hideout benches** with upgrade requirements
   - **Reverse recipe mapping**: Shows which items use this material
   - **Hideout usage mapping**: Shows bench requirements by level

## Overlay Information Display

The modern, interactive overlay displays:

- **Item Image** (200x200px max, high quality)
- **Item Name** with rarity-based color coding
- **Type & Rarity Badge**
- **Properties**: Weight, stack size, in-game value
- **Crafting Recipe**: Required materials + craft bench name (clickable)
- **Recycles Into**: Base recycling output (clickable)
- **Salvages Into**: Combat salvage output (clickable)
- **Used To Craft**: Reverse lookup - items that use this material (clickable)
- **Hideout Usage**: Bench upgrade requirements by level (clickable)

**Interactive Features:**
- Click any material to open its information in a new window
- Drag overlay by header to reposition
- Scroll with mouse wheel for long content
- Press `ESC` or click outside to close
- Multi-window support for exploring crafting chains

## Supported Languages

**22 languages supported** for UI and item data:

`en` (English), `de` (German), `fr` (French), `es` (Spanish), `pt` (Portuguese), `pl` (Polish), `no` (Norwegian), `da` (Danish), `it` (Italian), `ru` (Russian), `ja` (Japanese), `zh-TW` (Traditional Chinese), `uk` (Ukrainian), `zh-CN` (Simplified Chinese), `kr` (Korean), `tr` (Turkish), `hr` (Croatian), `sr` (Serbian)

## Building Executable

Create distributable executables using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build release version (no console)
python -m PyInstaller ArcHelper.spec --clean

# Build debug version (with console)
python -m PyInstaller ArcHelperDebug.spec --clean
```

Build output:
- `dist/ArcHelper.exe` - Release build (~66 MB, GUI only)
- `dist/ArcHelperDebug.exe` - Debug build (~66 MB, includes console)

**Notes:**
- `Data/` folder is automatically packaged
- `settings.json` and `Debug/` created next to exe at runtime
- Portable - no installation required
- Run as administrator for global hotkey support

## Troubleshooting

### Hotkey not working
- **Run as Administrator** (required for global hotkeys)
- Check if another application uses the same hotkey
- Change hotkey in Settings GUI or `settings.json`
- Verify keyboard library is working (check console output)

### Item not recognized
- Ensure item icon is **fully visible** and centered under cursor
- Check icon size matches configured capture size (default: 160x160px)
- Verify item is in the database (448 items currently supported)
- Check `Debug/` folder for captured screenshots
- Lower `MATCH_THRESHOLD` in `src/config.py` (default: 0.4)
- Console shows top 3 matches when recognition fails

### Overlay doesn't appear
- Check if window appeared off-screen (try dragging from screen edges)
- Verify tkinter is installed: `python -c "import tkinter"`
- Look for error messages in console
- Check if overlay was closed too quickly (loading spinner)

### Item data missing warning
- Error overlay shows: "Item data not found for ID: [item_id]"
- Check if JSON file exists in `Data/Items/[item_id].json`
- Verify JSON file contains correct `id` field
- Some items may not be implemented yet (expected warning)

### Performance issues
- Close other overlays/applications
- Reduce capture size in settings
- Check Debug screenshots for quality issues
- Verify system meets requirements (Windows 10+, 8GB RAM recommended)

## Performance Metrics

Expected performance on modern hardware:
- **Initialization**: ~3-5 seconds (load 448 items + templates)
- **Hotkey to overlay**: ~300-500ms total
  - Screen capture: <10ms
  - Image recognition: 200-400ms (multi-method comparison against 448 templates)
  - Overlay rendering: <50ms
- **Memory usage**: ~150-200 MB
- **CPU usage**: Minimal when idle, brief spike during recognition

## Development Status

**Version 1.0 - Production Ready**

✅ **Implemented Features:**
- Advanced multi-method image recognition (5 techniques)
- Comprehensive item database (448 items)
- Hideout bench integration (9 benches)
- Reverse recipe mapping (material → items)
- Interactive overlay UI with multi-window support
- Customizable settings with GUI
- Multi-language support (22 languages)
- Global hotkey with debouncing
- DPI-aware screen capture
- PyInstaller executable builds
- Debug screenshot saving

⚠️ **Known Limitations:**
- Windows only (due to pywin32 and keyboard library)
- Requires administrator privileges for global hotkeys
- Fixed capture size (must match in-game icon size)
- Not tested against actual game anti-cheat

🔮 **Future Enhancements:**
- In-game anti-cheat compatibility testing
- Performance optimizations
- Custom overlay themes
- Auto-update mechanism
- Additional recognition methods (AKAZE)
- Configurable confidence threshold in GUI

## Contributing

Contributions welcome! Please follow these guidelines:

1. **Maintain anti-cheat safety** - Never add features that hook, inject, or read game memory
2. **Test thoroughly** - Use test scripts and verify Debug screenshots
3. **Update localization** - Add new UI text to all 22 languages
4. **Document changes** - Update README.md and CLAUDE.md
5. **Preserve thread safety** - Use proper locking for shared resources

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

This is a community tool for Ark Raiders players.

**MIT License** - Free to use, modify, and distribute.

## Disclaimer

**Important:** This tool uses screen capture and overlay rendering only.

✅ **What it does:**
- Captures screenshots of your screen
- Displays information in a separate window
- Does NOT interact with the game

⚠️ **Use at your own risk:**
- Check game terms of service before using
- Report any issues or concerns immediately
- No warranty or guarantee provided

**The developers are not responsible for any consequences of using this tool.**

## Support

- **Issues**: Report bugs on GitHub Issues
- **Documentation**: See [CLAUDE.md](CLAUDE.md) for technical details
- **Community**: Share feedback and suggestions

## Credits

- **Item Data**: Sourced from Ark Raiders game files
- **Image Recognition**: OpenCV library
- **UI Framework**: Python tkinter
- **Screen Capture**: mss library

---

**Made with ❤️ for the Ark Raiders community**
