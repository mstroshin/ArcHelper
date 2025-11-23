"""
Test script for image recognition functionality.
"""

import sys
import cv2
from pathlib import Path
from src.data_loader import ItemDatabase
from src.image_recognition import ItemRecognizer

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_image_recognition():
    """Test the image recognition system."""

    print("=" * 60)
    print("Testing Image Recognition System")
    print("=" * 60)

    # Initialize database
    print("\n1. Loading item database...")
    data_dir = Path(__file__).parent / "Data"
    db = ItemDatabase(data_dir)
    db.load_all_items()
    print(f"   ✓ Loaded {len(db.items)} items")

    # Initialize recognizer
    print("\n2. Loading image templates...")
    recognizer = ItemRecognizer(data_dir, db)
    recognizer.load_templates()
    print(f"   ✓ Loaded {len(recognizer.templates)} templates")

    # Test recognition with an actual template image
    print("\n3. Testing recognition with template images...")

    # Get a few test images
    test_items = ['adrenaline_shot', 'arc_alloy', 'bandage', 'battery', 'chemicals']
    images_dir = data_dir / "Items" / "Images"

    for item_id in test_items:
        image_path = images_dir / f"{item_id}.png"

        if not image_path.exists():
            print(f"   ⚠ Image not found: {image_path.name}")
            continue

        # Load the image
        test_image = cv2.imread(str(image_path))

        if test_image is None:
            print(f"   ✗ Failed to load: {image_path.name}")
            continue

        # Recognize
        result = recognizer.recognize_with_score(test_image)

        if result:
            recognized_id, score = result
            item_data = db.get_item(recognized_id)

            if recognized_id == item_id:
                print(f"   ✓ {item_id}: Correctly recognized as '{item_data['name']['en']}' (score: {score:.4f})")
            else:
                print(f"   ✗ {item_id}: Incorrectly recognized as '{item_data['name']['en']}' (score: {score:.4f})")

                # Show top 3 matches for debugging
                top_matches = recognizer.get_top_matches(test_image, 3)
                print(f"      Top 3 matches:")
                for match_id, match_score in top_matches:
                    match_item = db.get_item(match_id)
                    match_name = match_item['name']['en'] if match_item else match_id
                    print(f"        - {match_name} ({match_id}): {match_score:.4f}")
        else:
            print(f"   ✗ {item_id}: Not recognized")

    # Test with top matches
    print("\n4. Testing top matches for 'adrenaline_shot'...")
    test_image_path = images_dir / "adrenaline_shot.png"

    if test_image_path.exists():
        test_image = cv2.imread(str(test_image_path))
        top_matches = recognizer.get_top_matches(test_image, 5)

        print("   Top 5 matches:")
        for idx, (item_id, score) in enumerate(top_matches, 1):
            item_data = db.get_item(item_id)
            item_name = item_data['name']['en'] if item_data else item_id
            print(f"   {idx}. {item_name} ({item_id}): {score:.4f}")

    print("\n" + "=" * 60)
    print("✓ Image recognition tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_image_recognition()
