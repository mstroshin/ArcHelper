"""Test overlay close behavior."""

import sys
import time
from src.data_loader import ItemDatabase
from src.overlay import OverlayUI

def test_overlay_close():
    """Test the overlay close behavior."""
    print("Loading item database...")
    db = ItemDatabase()
    db.load_items()

    # Get a test item
    test_item = db.get_item('scrap_grenade')
    if not test_item:
        # Try to get any item
        all_items = list(db.items.values())
        if all_items:
            test_item = all_items[0]
        else:
            print("No items found in database!")
            return

    print(f"Using test item: {test_item.get('id', 'Unknown')}")

    # Create overlay
    print("Creating overlay...")
    overlay = OverlayUI(db, language='ru')

    # Show overlay without auto-close (duration=0 by default)
    print("\n" + "=" * 60)
    print("Testing new close behavior:")
    print("- No auto-close timer")
    print("- Click on overlay: should NOT close")
    print("- Click outside overlay: should close")
    print("- Press ESC: should close")
    print("- Click X button: should close")
    print("=" * 60 + "\n")

    overlay.show(test_item)

    print("Overlay is now displayed.")
    print("Test the close behavior manually:")
    print("  1. Try clicking on the overlay (should stay open)")
    print("  2. Try clicking outside the overlay (should close)")
    print("  3. Try pressing ESC (should close)")
    print("  4. Try clicking the X button (should close)")
    print("\nWaiting 30 seconds before cleanup...")

    # Keep running for 30 seconds
    time.sleep(30)

    print("\nCleaning up...")
    overlay.cleanup()
    print("Test complete!")

if __name__ == "__main__":
    test_overlay_close()
