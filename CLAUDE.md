# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArcHelperPy is a **production-ready** game overlay assistant for Ark Raiders that helps players identify items and understand their crafting recipes, recycling components, and hideout bench usage. The application runs as a non-intrusive overlay on Windows:

- Players hover their mouse over an item in-game and press a hotkey (default: `ctrl+d`)
- The program captures the item icon (160x160px centered on cursor)
- Advanced multi-method image recognition identifies the item
- A modern overlay displays comprehensive information about the item

**Critical constraint**: The application does not interfere with the game or trigger anti-cheat systems. It is a passive overlay tool that uses only screen capture and GUI rendering.

## Technology Stack

- **Language**: Python 3.13
- **Target Platform**: Windows (requires administrator privileges for global hotkeys)
- **GUI Framework**: tkinter (overlay and settings windows)
- **Image Processing**: OpenCV, Pillow
- **Screen Capture**: mss
- **Hotkey Detection**: keyboard library
- **Windows API**: pywin32

### Dependencies (requirements.txt)
```
opencv-python>=4.8.0      # Multi-method image recognition
Pillow>=10.0.0            # Image loading (WebP, PNG, JPG support)
numpy>=1.24.0             # Array operations
mss>=9.0.0                # Fast screen capture
keyboard>=0.13.5          # Global hotkey detection
pywin32>=306              # Windows API access
```

## Project Structure

```
ArcHelperPy/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── settings.json             # User settings (auto-generated)
├── src/
│   ├── config.py             # Configuration constants
│   ├── data_loader.py        # ItemDatabase class (items + hideout benches)
│   ├── image_recognition.py  # Multi-method image matching
│   ├── screen_capture.py     # Screen capture with DPI awareness
│   ├── hotkey_manager.py     # Global hotkey registration
│   ├── overlay.py            # Modern overlay UI system
│   ├── settings_manager.py   # Settings persistence
│   ├── settings_gui.py       # Settings configuration window
│   └── localization.py       # Multi-language UI text (22 languages)
├── Data/
│   ├── Items/                # 448 item JSON files
│   │   └── Images/           # Item icons (WebP format, 160x160px)
│   └── Hideout/              # 9 hideout bench JSON files
├── Debug/                    # Captured screenshots for debugging
└── test_*.py                 # Component test scripts
```

## Data Architecture

### Item Data Structure

The project contains **448 game items** stored in `Data/Items/` with two components per item:
- **JSON file**: Complete item metadata (`Data/Items/<item_id>.json`)
- **WebP icon**: Item image for recognition (`Data/Items/Images/<item_id>.webp`, 160x160px)

**Note**: Some items (weapons with tiers) have separate JSON files with suffixes (`_i`, `_ii`, `_iii`, `_iv`) but share the same base image file without the suffix.

### JSON Schema

Each item JSON follows this structure:

```json
{
  "id": "unique_item_id",
  "name": { "en": "English Name", ... },  // Multilingual support (22 languages)
  "description": { "en": "Description", ... },
  "type": "Item Type",  // e.g., "Quick Use", "Topside Material"
  "rarity": "Common|Uncommon|Rare|Epic|Legendary|...",
  "value": 300,  // In-game value
  "weightKg": 0.2,
  "stackSize": 5,

  // Crafting and recycling relationships
  "recipe": { "material1": count, "material2": count },  // Optional: ingredients needed to craft this item
  "craftBench": "bench_id",  // Optional: required crafting station
  "recyclesInto": { "material1": count, "material2": count },  // Optional: items obtained when recycled
  "salvagesInto": { "material1": count },  // Optional: items obtained when salvaged

  // Additional metadata
  "effects": { ... },  // Optional: item effects with values
  "imageFilename": "https://cdn.arctracker.io/items/<item_id>.png",
  "updatedAt": "MM/DD/YYYY"
}
```

**Key relationships**:
- `recipe`: Shows what materials are needed to craft this item
- `craftBench`: The crafting station required (e.g., "med_station", "workbench")
- `recyclesInto`: Materials obtained when recycling the item (disassembling)
- `salvagesInto`: Materials obtained when salvaging the item (alternative breakdown method)

### Hideout Bench Data

The project includes **9 hideout benches** stored in `Data/Hideout/`:
- equipment_bench
- explosives_bench
- med_station
- refiner
- scrappy
- stash
- utility_bench
- weapon_bench
- workbench

Each bench JSON contains upgrade requirements organized by level:
```json
{
  "id": "bench_id",
  "name": { "en": "Bench Name", ... },
  "levels": {
    "1": { "item_id": count, ... },
    "2": { "item_id": count, ... }
  }
}
```

## Core Features (Implemented)

### 1. Advanced Image Recognition System
**Location**: [src/image_recognition.py](src/image_recognition.py)

**Multi-method weighted scoring** (5 techniques combined):
1. Template Matching (TM_CCOEFF_NORMED) - Weight: 25%
2. Correlation Coefficient (TM_CCORR_NORMED) - Weight: 15%
3. Histogram-Equalized Matching - Weight: 30% (lighting invariant)
4. Color Histogram Comparison - Weight: 15%
5. ORB Feature Matching - Weight: 15% (feature-based, 500 features)

**Features**:
- Confidence threshold: 0.4 (40%)
- Automatic image resizing to 160x160px
- Supports WebP, PNG, and JPG formats
- Debug screenshots saved to `Debug/` folder
- Cancellation support to prevent wasted processing
- Top 3 matches logged on failure

### 2. Modern Overlay UI System
**Location**: [src/overlay.py](src/overlay.py)

**Three overlay types**:
- **Loading overlay**: Progress bar while recognizing
- **Item overlay**: Comprehensive item information
- **Error overlay**: Recognition failures

**Advanced UI features**:
- Borderless, semi-transparent (97% opacity)
- Scrollable content with custom scrollbar
- Draggable by header
- Clickable materials (spawns new overlay windows)
- Rarity-based color coding
- Item image display (200x200px max)
- Outside-click detection to close
- Multi-window support (primary + spawned windows)
- ESC key to close

**Information displayed**:
- Item name with rarity color
- Item image
- Type and rarity badge
- Properties (weight, stack size, value)
- **Crafting recipe** with craft bench name
- **Recycles into** (base recycling)
- **Salvages into** (combat salvage)
- **Used to craft** (reverse lookup - items that use this material)
- **Hideout usage** (bench requirements by level)

### 3. Settings System
**Location**: [src/settings_manager.py](src/settings_manager.py), [src/settings_gui.py](src/settings_gui.py)

**Persistent settings** stored in `settings.json`:
```json
{
  "language": "en",
  "capture_size": [160, 160],
  "recognition_hotkey": "ctrl+d"
}
```

**Settings GUI** (non-blocking window):
- Language selection (22 languages)
- Screenshot size (50-500px slider)
- Hotkey customization with recorder
- Automatic validation and defaults

### 4. Screen Capture
**Location**: [src/screen_capture.py](src/screen_capture.py)

**Features**:
- MSS-based fast screen capture
- DPI awareness for accurate positioning
- Cursor position detection (win32api)
- Configurable capture size (default: 160x160px)
- Centered on cursor position
- Thread-safe context managers
- Multiple monitor support

### 5. Hotkey Management
**Location**: [src/hotkey_manager.py](src/hotkey_manager.py)

**Features**:
- Global hotkey detection (default: `ctrl+d`)
- Administrator privilege checking
- Customizable combinations
- Non-suppressing (doesn't block game input)
- Clean unregistration
- Thread-safe callback handling

### 6. Multi-language Support
**Location**: [src/localization.py](src/localization.py)

**22 languages supported**:
`en, de, fr, es, pt, pl, no, da, it, ru, ja, zh-TW, uk, zh-CN, kr, tr, hr, sr`

**Localized elements**:
- All overlay UI labels and sections
- Settings window text
- Error messages
- Status indicators
- Instructions

### 7. Data Management
**Location**: [src/data_loader.py](src/data_loader.py)

**ItemDatabase class** provides:
- Load all 448 item JSON files
- Load 9 hideout bench definitions
- Build reverse recipe mapping (material → items that use it)
- Build hideout usage mapping (item → bench requirements by level)
- Multi-language name support
- Search by name functionality
- Efficient indexing by item ID

## Application Workflow

### Startup Sequence
1. Load settings from `settings.json` (or create defaults)
2. Check administrator privileges (warn if not admin)
3. Load 448 items from `Data/Items/*.json`
4. Build reverse recipe mappings
5. Load hideout bench data from `Data/Hideout/*.json`
6. Build hideout usage mappings
7. Load item icon templates from `Data/Items/Images/*.webp`
8. Initialize ORB feature detector for image recognition
9. Setup screen capture with DPI awareness
10. Create overlay UI manager
11. Register global hotkey
12. Show settings window (non-blocking)
13. Enter hotkey listener loop

### Recognition Workflow
1. User hovers over item and presses hotkey (`ctrl+d`)
2. Show loading overlay immediately
3. Capture 160x160px region centered on cursor (threaded)
4. Save debug screenshot to `Debug/capture_YYYYMMDD_HHMMSS.png`
5. Perform multi-method recognition:
   - Resize captured image to 160x160px
   - Convert to grayscale
   - Apply histogram equalization
   - Calculate color histogram
   - Extract ORB features
   - Compare against all templates using 5 methods
   - Calculate weighted score
6. If best match score >= 0.4 (40%):
   - Retrieve item data from database
   - Show item overlay with all information
7. If not recognized:
   - Show "Item not recognized" error overlay
   - Print top 3 matches to console for debugging

### Overlay Interaction
- **ESC key**: Close overlay
- **Click outside**: Close all overlay windows
- **Click material**: Spawn new overlay window for that item
- **Drag header**: Move overlay window
- **Mouse wheel**: Scroll content
- **X button**: Close overlay

## Development Notes

### Image Recognition
- Icons are stored as **WebP format** (160x160px) for smaller file size
- Multi-method approach handles lighting variations and partial occlusions
- ORB features provide rotation/scale invariance
- Histogram equalization improves matching in different lighting
- Confidence threshold can be adjusted in [src/config.py](src/config.py)

### Data Loading
The `ItemDatabase` class builds several indexes on startup:
- **Item ID → Item data**: Fast lookup after recognition
- **Material ID → Items that use it**: For "Used to craft" section
- **Item ID → Hideout bench requirements**: For hideout upgrade planning

### Language Support
- Item names/descriptions come from item JSON files (22 languages)
- UI text comes from [src/localization.py](src/localization.py)
- Language setting persists in `settings.json`

### Thread Safety
- Screen capture uses context managers for cleanup
- GUI operations queued and executed in GUI thread
- Recognition runs in background thread to keep UI responsive
- Cancellation events prevent processing when overlay closes

### Anti-Cheat Safety

**The application follows strict anti-cheat guidelines**:
- ✅ Does NOT hook into game process memory
- ✅ Does NOT inject any DLLs into the game
- ✅ Does NOT read game memory
- ✅ Uses only screen capture (mss library)
- ✅ Renders overlay in separate process
- ✅ Non-suppressing hotkeys (game receives input)
- ✅ No interaction with game files or process

**The application is purely passive**: it watches the screen and displays information in a separate window, similar to a second monitor or overlay like Discord/OBS.

## Configuration

### Key Constants ([src/config.py](src/config.py))
```python
DEFAULT_HOTKEY = 'ctrl+shift+i'      # Default hotkey (overridden by settings)
ICON_SIZE = (160, 160)               # Item icon size
MATCH_THRESHOLD = 0.4                # Recognition confidence threshold (40%)
CAPTURE_SIZE = (160, 160)            # Default screen capture size
OVERLAY_WIDTH = 620                  # Overlay window width
OVERLAY_HEIGHT = 650                 # Overlay window height
OVERLAY_ALPHA = 0.97                 # Overlay transparency (97% opaque)
DEFAULT_LANGUAGE = 'en'              # Default UI language
```

### User Settings (settings.json)
Users can customize:
- **language**: UI language (22 options)
- **capture_size**: Screenshot size in pixels (50-500)
- **recognition_hotkey**: Custom hotkey combination

## Testing

Test scripts are provided for individual components:
- `test_recognition.py` - Image recognition testing
- `test_settings.py` - Settings manager testing
- `test_hotkey.py` - Hotkey detection testing
- `test_settings_gui.py` - Settings GUI testing
- `test_overlay_close.py` - Overlay closing behavior
- `test_simple_load.py` - Data loading test
- `test_minimal_gui.py` - Minimal GUI test

## Build System

PyInstaller spec files for distribution:
- `ArcHelper.spec` - Release build
- `ArcHelperDebug.spec` - Debug build with console

Build outputs:
- `build/` - Build artifacts
- `dist/` - Distributable executables

## Known Limitations

1. **Requires administrator privileges** for global hotkey registration
2. **Windows only** due to pywin32 and keyboard library dependencies
3. **Fixed capture size** (160x160px) - must match in-game icon size
4. **Not tested against actual game anti-cheat** - use at own risk

## Future Enhancements

Potential improvements:
- In-game testing for anti-cheat compatibility verification
- Performance optimization for faster recognition
- Custom overlay themes and colors
- Separate hotkey for settings window
- Auto-update mechanism
- Additional recognition methods (SIFT, AKAZE)
- Configurable confidence threshold in settings

## Contributing Guidelines

When modifying this codebase:

1. **Maintain anti-cheat safety**: Never add features that hook, inject, or read game memory
2. **Test thoroughly**: Use test scripts and verify in Debug/ folder
3. **Update localization**: Add new UI text to all 22 languages in [src/localization.py](src/localization.py)
4. **Document changes**: Update this file when adding features or changing architecture
5. **Preserve thread safety**: Use proper locking for shared resources
6. **Handle errors gracefully**: Show error overlays instead of crashing
7. **Keep UI responsive**: Run heavy operations in background threads
