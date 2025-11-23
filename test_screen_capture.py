"""
Test script for screen capture functionality.
"""

import sys
import cv2
import time
from pathlib import Path
from src.screen_capture import ScreenCapture

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_screen_capture():
    """Test the screen capture system."""

    print("=" * 60)
    print("Testing Screen Capture System")
    print("=" * 60)

    # Initialize screen capture
    print("\n1. Initializing screen capture...")
    capture = ScreenCapture()
    print("   ✓ Screen capture initialized")

    # Get monitor info
    print("\n2. Getting monitor information...")
    monitors = capture.get_monitor_info()
    print(f"   ✓ Found {len(monitors) - 1} monitor(s)")  # -1 because index 0 is all monitors

    for i, monitor in enumerate(monitors):
        if i == 0:
            print(f"   Monitor {i} (All): {monitor}")
        else:
            print(f"   Monitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")

    # Test cursor position
    print("\n3. Testing cursor position detection...")
    cursor_pos = capture.get_cursor_position()
    print(f"   ✓ Current cursor position: {cursor_pos}")

    # Test capture at cursor
    print("\n4. Testing screen capture at cursor position...")
    print("   Move your cursor to any position and press Enter...")
    input("   Press Enter to capture...")

    img = capture.capture_at_cursor()

    if img is not None:
        print(f"   ✓ Captured image: {img.shape[1]}x{img.shape[0]} pixels")

        # Save the captured image
        output_path = Path("test_capture.png")
        cv2.imwrite(str(output_path), img)
        print(f"   ✓ Saved captured image to: {output_path}")

        # Display image statistics
        print(f"   Image statistics:")
        print(f"     - Mean pixel value: {img.mean():.2f}")
        print(f"     - Min pixel value: {img.min()}")
        print(f"     - Max pixel value: {img.max()}")
    else:
        print("   ✗ Failed to capture image")

    # Test full screen capture
    print("\n5. Testing full screen capture...")
    full_screen = capture.capture_full_screen(1)

    if full_screen is not None:
        print(f"   ✓ Captured full screen: {full_screen.shape[1]}x{full_screen.shape[0]} pixels")

        # Save the full screen capture
        output_path = Path("test_fullscreen.png")
        cv2.imwrite(str(output_path), full_screen)
        print(f"   ✓ Saved full screen capture to: {output_path}")
    else:
        print("   ✗ Failed to capture full screen")

    # Test region capture
    print("\n6. Testing region capture (100x100 at top-left corner)...")
    region = capture.capture_region(0, 0, 100, 100)

    if region is not None:
        print(f"   ✓ Captured region: {region.shape[1]}x{region.shape[0]} pixels")
    else:
        print("   ✗ Failed to capture region")

    # Cleanup
    print("\n7. Cleaning up...")
    capture.cleanup()
    print("   ✓ Cleanup complete")

    print("\n" + "=" * 60)
    print("✓ Screen capture tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_screen_capture()
