# Testing Guide for ArcHelperPy

This document describes how to test the ArcHelperPy application.

## Prerequisites

1. Python 3.13 installed
2. Dependencies installed: `py -m pip install -r requirements.txt`
3. Administrator privileges (recommended for global hotkeys)

## Unit Tests

### 1. Test Data Loader
Tests loading of 448 item JSON files and reverse recipe mapping.

```bash
py test_data_loader.py
```

**Expected output:**
- ✓ All 448 items loaded
- ✓ Item retrieval works (example: adrenaline_shot)
- ✓ Reverse mapping finds items using materials
- ✓ Search by name works
- ✓ Statistics show correct data structure

### 2. Test Image Recognition
Tests loading and matching of item icon templates.

```bash
py test_image_recognition.py
```

**Expected output:**
- ✓ 270 icon templates loaded
- ✓ Perfect recognition (score: 1.0000) for template images
- ✓ Top matches show reasonable similarities

### 3. Test Screen Capture
Tests screen capture functionality at cursor position.

```bash
py test_screen_capture.py
```

**Expected output:**
- ✓ Monitor information displayed
- ✓ Cursor position detected
- ✓ Screen captured and saved to test_capture.png
- ✓ Full screen capture saved to test_fullscreen.png

**Note:** This test requires user interaction (pressing Enter to capture).

### 4. Test Overlay UI
Tests the overlay window display.

```bash
py test_overlay.py
```

**Expected output:**
- ✓ Overlay window appears near cursor
- ✓ Item information displayed correctly
- ✓ Window closes on ESC, click, or after 10 seconds

### 5. Test Interactive Query
Interactive tool to query item information by ID or name.

```bash
py test_simple.py
```

**Usage:**
- Enter item ID (e.g., `adrenaline_shot`, `arc_alloy`)
- View complete item information
- Type `quit` to exit

## Integration Testing

### Full Application Test

Run the full application:

```bash
py main.py
```

**Note:** Run as Administrator for best hotkey performance:
```bash
# Right-click Command Prompt → Run as Administrator
py main.py
```

**Expected output:**
```
============================================================
ArcHelperPy - Initializing...
============================================================

Checking administrator privileges...
Running with administrator privileges ✓

Loading item database...
✓ Loaded 448 items

Loading item icons for recognition...
✓ Loaded 270 icon templates

Initializing screen capture...
✓ Screen capture ready

Initializing overlay UI...
✓ Overlay UI ready

Setting up hotkey manager...
Registered hotkey: ctrl+shift+i
✓ Hotkey registered

============================================================
✓ Initialization complete!
============================================================

📋 Usage:
  1. Hover your cursor over an item in-game
  2. Press Ctrl+Shift+I to identify the item
  3. View item information in the overlay
  4. Press ESC or click to close the overlay

Press Ctrl+C to exit the application
```

### Testing Without the Game

Since the game might not be running during development, you can test using the icon images:

1. Start the application: `py main.py`
2. Open an image file from `Data/Items/Images/` in any image viewer
3. Hover your cursor over the item icon in the image
4. Press `Ctrl+Shift+I`
5. The overlay should appear showing item information

**Good test images:**
- `Data/Items/Images/adrenaline_shot.png` - Has recipe, recycles, salvages
- `Data/Items/Images/arc_alloy.png` - Used in multiple crafting recipes
- `Data/Items/Images/bandage.png` - Simple medical item

## Anti-Cheat Compatibility Testing

### Safety Checklist

Before testing with the actual game, verify:

- [ ] Application runs as a separate process (not injecting into game)
- [ ] Only uses screen capture (no memory reading)
- [ ] No DLL injection
- [ ] No process hooking
- [ ] Overlay is a separate window (not drawn directly on game)

### Testing Approach

1. **Without Game Running:**
   - Test all components work correctly
   - Verify screen capture and overlay functionality

2. **With Game Running (Caution):**
   - Start the game first
   - Then start ArcHelperPy
   - Test hotkey functionality
   - Verify overlay appears over the game
   - Monitor for any anti-cheat warnings

3. **Monitor for Issues:**
   - Game crashes
   - Anti-cheat warnings
   - Connection issues
   - Performance degradation

### Safety Notes

- **Start conservatively:** Test in offline mode or practice areas first
- **Monitor behavior:** Watch for any anti-cheat system reactions
- **Have a backup:** Be prepared to close the application immediately
- **User responsibility:** This tool is provided as-is. Users are responsible for checking game terms of service

## Known Limitations

1. **Administrator Privileges:** Global hotkeys work best with admin rights
2. **Image Recognition:** Requires items to be displayed at 200x200px size
3. **Performance:** Comparing against 270 templates may take ~100-200ms
4. **Overlay Positioning:** May not work perfectly on multi-monitor setups

## Troubleshooting

### Hotkey not working
- Run as Administrator
- Check if another application is using `Ctrl+Shift+I`
- Try a different hotkey in `src/config.py`

### Image recognition fails
- Verify item icon is visible and not obscured
- Check image size matches ICON_SIZE in config
- Lower MATCH_THRESHOLD in config (default: 0.8)

### Overlay doesn't appear
- Check if overlay is appearing off-screen
- Verify tkinter is working: `py -c "import tkinter; tkinter.Tk()"`
- Check for errors in console output

### Screen capture fails
- Verify mss library is installed
- Check monitor configuration
- Try capturing full screen first (test_screen_capture.py)

## Performance Benchmarks

Expected performance on modern hardware:
- Data loading: < 2 seconds
- Template loading: < 3 seconds
- Screen capture: < 10ms
- Image recognition: 100-200ms (270 templates)
- Overlay display: < 100ms

Total time from hotkey press to overlay: ~300-400ms
