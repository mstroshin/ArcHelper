"""
Test script for item recognition accuracy.

This script tests the image recognition system against screenshots from TestImages folder.
The item name in the screenshot filename should match the recognized item name.
"""

import sys
import io
from pathlib import Path
import cv2

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from src.data_loader import ItemDatabase
from src.image_recognition import ItemRecognizer


def normalize_name(name: str) -> str:
    """
    Normalize a name for comparison by converting to lowercase and replacing
    underscores/hyphens with spaces.

    Args:
        name: The name to normalize

    Returns:
        Normalized name string
    """
    return name.lower().replace('_', ' ').replace('-', ' ').strip()


def run_recognition_tests():
    """Run recognition tests on all images in TestImages folder."""

    print("\n" + "=" * 70)
    print("ArcHelperPy - Recognition Test Suite")
    print("=" * 70 + "\n")

    # Setup paths
    project_root = Path(__file__).parent
    data_dir = project_root / "Data"
    test_images_dir = project_root / "TestImages"

    if not test_images_dir.exists():
        print(f"❌ TestImages directory not found: {test_images_dir}")
        return

    # Load item database
    print("Loading item database...")
    database = ItemDatabase(data_dir)
    database.load_all_items()
    print(f"✓ Loaded {len(database.items)} items\n")

    # Initialize recognizer
    print("Loading item icon templates...")
    recognizer = ItemRecognizer(data_dir, database)
    recognizer.load_templates()
    print(f"✓ Loaded {len(recognizer.templates)} templates\n")

    # Get all test images
    test_images = list(test_images_dir.glob("*.png")) + list(test_images_dir.glob("*.jpg"))

    if not test_images:
        print(f"❌ No test images found in {test_images_dir}")
        return

    print(f"Found {len(test_images)} test image(s)\n")
    print("=" * 70)

    # Track results
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    # Process each test image
    for test_image_path in sorted(test_images):
        total_tests += 1

        # Extract expected item name from filename (without extension)
        expected_name = normalize_name(test_image_path.stem)

        print(f"\nTest {total_tests}: {test_image_path.name}")
        print(f"  Expected: '{expected_name}'")

        # Load the test image
        test_image = cv2.imread(str(test_image_path), cv2.IMREAD_COLOR)

        if test_image is None:
            print(f"  ❌ FAILED: Could not load image")
            failed_tests += 1
            continue

        print(f"  Image size: {test_image.shape[1]}x{test_image.shape[0]}")

        # Run recognition - get top 150 matches to find the correct item
        top_matches = recognizer.get_top_matches(test_image, 150)

        # Display top 10 matches
        print(f"  Top 10 matches:")
        found_match = False
        match_position = -1
        match_confidence = 0.0

        # Check all 50 matches for expected item
        for i, (match_id, match_score) in enumerate(top_matches, 1):
            match_item = database.get_item(match_id)
            if match_item:
                match_name = match_item['name']['en']
                normalized_match = normalize_name(match_name)

                # Check if this is our expected item
                is_expected = (expected_name == normalized_match or
                              expected_name in normalized_match or
                              normalized_match in expected_name)

                # Display only top 10
                if i <= 10:
                    marker = " ← EXPECTED" if is_expected else ""
                    print(f"    {i}. {match_name}: {match_score:.2%}{marker}")

                if is_expected and not found_match:
                    found_match = True
                    match_position = i
                    match_confidence = match_score

        # Determine pass/fail - ONLY rank #1 is considered a pass
        if found_match:
            if match_position == 1:
                print(f"  ✓ PASSED: Perfect match at rank #1 ({match_confidence:.2%})")
                passed_tests += 1
            else:
                print(f"  ❌ FAILED: Expected item found at rank #{match_position} (must be #1 to pass)")
                print(f"    Confidence: {match_confidence:.2%}")
                failed_tests += 1
        else:
            print(f"  ❌ FAILED: Expected item '{expected_name}' not in top 150 matches")
            failed_tests += 1

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total tests:  {total_tests}")
    print(f"✓ Passed:     {passed_tests} ({passed_tests/total_tests*100:.1f}%)" if total_tests > 0 else "✓ Passed:     0")
    print(f"❌ Failed:     {failed_tests} ({failed_tests/total_tests*100:.1f}%)" if total_tests > 0 else "❌ Failed:     0")
    print("=" * 70 + "\n")

    # Return exit code based on results
    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = run_recognition_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
