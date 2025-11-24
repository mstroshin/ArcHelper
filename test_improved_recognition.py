"""Test script for improved image recognition system."""

import cv2
import time
from pathlib import Path
from src.data_loader import ItemDatabase
from src.image_recognition import ItemRecognizer

def test_recognition():
    """Test the improved recognition system."""
    print("=" * 60)
    print("Testing Improved Image Recognition System")
    print("=" * 60)

    # Initialize database
    print("\n1. Loading item database...")
    start_time = time.time()
    db = ItemDatabase("Data")
    db.load_items()
    db.load_hideout_benches()
    print(f"   Loaded {len(db.items)} items in {time.time() - start_time:.2f}s")

    # Initialize recognizer
    print("\n2. Initializing recognizer...")
    start_time = time.time()
    recognizer = ItemRecognizer("Data", db)
    recognizer.load_templates()
    print(f"   Loaded templates in {time.time() - start_time:.2f}s")

    # Check if SIFT is available
    if recognizer.use_sift:
        print("   ✓ SIFT detector is available (enhanced accuracy)")
    else:
        print("   ⚠ SIFT detector not available (install opencv-contrib-python for better accuracy)")

    # Test with debug captures if available
    debug_dir = Path("Debug")
    if debug_dir.exists():
        test_images = list(debug_dir.glob("capture_*.png"))[:3]  # Test first 3 captures

        if test_images:
            print(f"\n3. Testing with {len(test_images)} captured images from Debug/...")

            for i, image_path in enumerate(test_images, 1):
                print(f"\n   Test {i}: {image_path.name}")
                print("   " + "-" * 50)

                # Load image
                image = cv2.imread(str(image_path))
                if image is None:
                    print("   ✗ Could not load image")
                    continue

                # Test adaptive recognition
                start_time = time.time()
                result = recognizer.recognize_adaptive(image)
                elapsed = time.time() - start_time

                print(f"   Recognition time: {elapsed:.2f}s")
                print(f"   Status: {result['status']}")
                print(f"   Item ID: {result['item_id']}")
                print(f"   Confidence: {result['confidence']:.1%}")

                if result['item_id'] and result['item_id'] in db.items:
                    item = db.items[result['item_id']]
                    item_name = item['name'].get('en', 'Unknown')
                    print(f"   Item Name: {item_name}")

                if result.get('score_details'):
                    details = result['score_details']
                    print(f"   Score breakdown:")
                    print(f"     - Histogram: {details.get('histogram', 0):.2f}")
                    print(f"     - Template (equalized): {details.get('template_equalized', 0):.2f}")
                    print(f"     - ORB features: {details.get('orb_features', 0):.2f}")
                    print(f"     - SIFT features: {details.get('sift_features', 0):.2f}")

                if result.get('alternatives'):
                    print(f"   Alternatives:")
                    for alt_id, alt_score in result['alternatives']:
                        if alt_id in db.items:
                            alt_name = db.items[alt_id]['name'].get('en', 'Unknown')
                            print(f"     - {alt_name} ({alt_id}): {alt_score:.1%}")
        else:
            print("\n3. No test images found in Debug/ folder")
            print("   Tip: Run the application and capture some items first")
    else:
        print("\n3. Debug/ folder not found")
        print("   Tip: Run the application and capture some items first")

    # Test with a specific item template
    print("\n4. Testing with random item template...")
    images_dir = Path("Data/Items/Images")
    if images_dir.exists():
        templates = list(images_dir.glob("*.webp"))[:1]  # Test with first template

        if templates:
            template_path = templates[0]
            print(f"   Using template: {template_path.stem}")

            from PIL import Image
            import numpy as np

            # Load template as test image
            pil_image = Image.open(str(template_path)).convert('RGB')
            test_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            # Test recognition
            start_time = time.time()
            result = recognizer.recognize_adaptive(test_image)
            elapsed = time.time() - start_time

            print(f"   Recognition time: {elapsed:.2f}s")
            print(f"   Expected: {template_path.stem}")
            print(f"   Got: {result['item_id']}")
            print(f"   Confidence: {result['confidence']:.1%}")

            if result['item_id'] == template_path.stem:
                print("   ✓ Perfect match!")
            else:
                print("   ✗ Mismatch detected")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_recognition()
