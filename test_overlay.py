"""
Test script for overlay UI functionality.
"""

import sys
from pathlib import Path
from src.data_loader import ItemDatabase
from src.overlay import OverlayUI

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_overlay():
    """Test the overlay UI."""

    print("=" * 60)
    print("Testing Overlay UI")
    print("=" * 60)

    # Load database
    print("\n1. Loading item database...")
    data_dir = Path(__file__).parent / "Data"
    db = ItemDatabase(data_dir)
    db.load_all_items()
    print(f"   ✓ Loaded {len(db.items)} items")

    # Initialize overlay
    print("\n2. Initializing overlay...")
    overlay = OverlayUI(db, language='en')
    print("   ✓ Overlay initialized")

    # Test with adrenaline_shot
    print("\n3. Displaying item: adrenaline_shot")
    print("   The overlay window will appear near your cursor")
    print("   You can:")
    print("     - Press ESC to close")
    print("     - Click anywhere to close")
    print("     - Wait 10 seconds for auto-close")
    print()

    item = db.get_item('adrenaline_shot')

    if item:
        overlay.show(item, duration=10)
    else:
        print("   ✗ Item not found!")

    print("\n" + "=" * 60)
    print("✓ Overlay test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_overlay()
