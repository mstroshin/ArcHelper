# ArcHelperPy

ArcHelperPy is a passive overlay assistant for Ark Raiders: press a hotkey while hovering an item in-game and instantly see its crafting recipe, recycling/salvage outputs, reverse usage, and hideout bench relevance.

## Core Features
- Item identification through combined image recognition (templates, histograms, features)
- Full item sheet: recipe, recycle, salvage, used-to-craft, hideout usage
- Multi-window exploration: click any material to open its own panel
- 22 UI languages (items + interface text)
- Configurable hotkey, capture size, language & thresholds
- Safe: screen capture only; no memory, hooks, injection, or suppression of input

## Demo

https://github.com/user-attachments/assets/arc_helper_0.1.2_vid.mp4

*Watch ArcHelper in action: hover over an item, press the hotkey, and instantly see detailed information.*

## Quick Start
1. Download a release (or build locally).
2. Run `ArcHelper.exe` (see Windows Defender note below).
3. Pick language, adjust hotkey (default `Ctrl+D`), optionally change capture size (default 160×160).
4. In-game: center cursor over item icon and press the hotkey. Overlay appears with details; click materials to drill down; press `ESC` to close.

### ⚠️ Windows Defender Warning
When running `ArcHelper.exe` for the first time, Windows may show **"Windows protected your PC"** warning. This is a false positive for unsigned applications.

**How to run safely:**
1. Click **"More info"**
2. Click **"Run anyway"**

**Why this happens:** ArcHelper is not code-signed with an expensive certificate (~$400/year). The application is safe—it only captures screenshots and displays overlays without touching game memory or files.

## Installation (Source)
```bash
git clone <repo>
pip install -r requirements.txt
python main.py
```
Run terminal as Administrator if hotkey fails.

## Troubleshooting (Brief)
- Hotkey fails: ensure Admin privileges; change hotkey if conflicting.
- No match: icon must be fully visible & sized like capture; lower `MATCH_THRESHOLD` in `src/config.py`.
- Overlay off-screen: drag from edges or reset display scaling.

## Safety
Passive overlay only: captures a small region around cursor, compares against packaged item templates, and renders separate windows. No interaction with game process or files.

## Build (PyInstaller)
```bash
pip install pyinstaller
python -m PyInstaller ArcHelper.spec --clean      # release (no console)
python -m PyInstaller ArcHelperDebug.spec --clean # debug (console)
```
Result: `dist/ArcHelper.exe` / `dist/ArcHelperDebug.exe`. Data folder bundled automatically; `settings.json` created at runtime. Debug screenshots saved only in dev mode (not in release builds).

## Technical Details
- Recognition blend (weighted): template correlation, equalized template, color histogram, ORB, optional fallbacks; configurable threshold (default 0.40).
- Data set: hundreds of item JSON definitions + icons (WebP 160×160) and hideout bench data. Reverse mappings precomputed for fast “Used To Craft”.
- Performance (typical): capture <10 ms, recognition 200–400 ms, render <50 ms.
- Platform: Windows (global hotkey + pywin32). Requires Admin for reliable system-wide hotkey.
- Localization: 22 languages via `localization.py`; new strings must be added for every locale.

## License & Credits
MIT License. Community tool; use at your own risk.
Data & inspiration thanks to:
- https://github.com/RaidTheory/arcraiders-data
- https://arctracker.io

Made with ❤️ for the Ark Raiders community.
