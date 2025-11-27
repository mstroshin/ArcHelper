"""Test script to verify white background removal on small icons."""

import cv2
import numpy as np
from pathlib import Path
from src.image_recognition import ItemRecognizer


def test_background_removal(image_path: str):
    """Test background removal on a single image."""
    print(f"\nTesting: {image_path}")
    print("=" * 60)

    # Load image
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        print(f"ERROR: Could not load image from {image_path}")
        return

    print(f"Original size: {image.shape[1]}x{image.shape[0]}")

    # Create recognizer instance (just for the background removal method)
    recognizer = ItemRecognizer("Data", None)

    # Test background removal
    processed = recognizer._remove_white_background(image)

    print(f"Processed size: {processed.shape[1]}x{processed.shape[0]}")

    # Analyze edges before/after
    def analyze_edges(img, label):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        top_edge = np.mean(gray[0:3, :])
        bottom_edge = np.mean(gray[-3:, :])
        left_edge = np.mean(gray[:, 0:3])
        right_edge = np.mean(gray[:, -3:])

        print(f"\n{label} edge brightness:")
        print(f"  Top:    {top_edge:.1f}")
        print(f"  Bottom: {bottom_edge:.1f}")
        print(f"  Left:   {left_edge:.1f}")
        print(f"  Right:  {right_edge:.1f}")
        print(f"  Light edges (>230): {sum([top_edge > 230, bottom_edge > 230, left_edge > 230, right_edge > 230])}/4")

    analyze_edges(image, "BEFORE")
    analyze_edges(processed, "AFTER")

    # Save processed image for visual inspection
    output_path = image_path.replace("testing_images", "testing_images/processed")
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(output_path, processed)
    print(f"\nProcessed image saved to: {output_path}")

    # Also save a comparison image (side by side)
    comparison = np.hstack([image, processed])
    comparison_path = image_path.replace("testing_images", "testing_images/comparison")
    comparison_dir = Path(comparison_path).parent
    comparison_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(comparison_path, comparison)
    print(f"Comparison image saved to: {comparison_path}")


if __name__ == "__main__":
    print("White Background Removal Test")
    print("=" * 60)

    test_images = [
        "testing_images/small_icon_1.png",
        "testing_images/small_icon_2.png"
    ]

    for image_path in test_images:
        if Path(image_path).exists():
            test_background_removal(image_path)
        else:
            print(f"\nWARNING: Image not found: {image_path}")

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("Check 'testing_images/processed/' for processed images")
    print("Check 'testing_images/comparison/' for side-by-side comparisons")
