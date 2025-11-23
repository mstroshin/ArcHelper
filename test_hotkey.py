"""Test hotkey registration and detection."""

import keyboard
import time

def test_hotkey():
    """Test if hotkey works."""
    print("Testing hotkey registration...")
    print("=" * 60)

    hotkey = "ctrl+d"
    triggered = [False]

    def on_trigger():
        triggered[0] = True
        print(f"\n✓ Hotkey '{hotkey}' triggered!")
        print("=" * 60)

    # Register hotkey
    try:
        keyboard.add_hotkey(hotkey, on_trigger, suppress=False)
        print(f"✓ Hotkey '{hotkey}' registered successfully")
        print(f"\nPress {hotkey.upper()} to test...")
        print("Press ESC to exit\n")

        # Wait for trigger or ESC
        while not triggered[0]:
            if keyboard.is_pressed('esc'):
                print("\nESC pressed, exiting...")
                break
            time.sleep(0.1)

        if triggered[0]:
            print("\n✓ Test PASSED - Hotkey is working!")
        else:
            print("\n✗ Test CANCELLED - Hotkey not triggered")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            keyboard.unhook_all()
        except:
            pass

if __name__ == "__main__":
    import ctypes
    import sys

    # Check if running as admin
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if is_admin:
            print("✓ Running with administrator privileges\n")
        else:
            print("⚠ WARNING: Not running as administrator!")
            print("  Global hotkeys may not work properly.\n")
    except:
        print("⚠ Could not check admin status\n")

    test_hotkey()
