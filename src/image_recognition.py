"""Image recognition module for identifying items."""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from src.config import MATCH_THRESHOLD, ICON_SIZE


class ItemRecognizer:
    """Recognizes items from captured images using template matching."""

    def __init__(self, data_dir, database):
        """
        Initialize the item recognizer.

        Args:
            data_dir: Path to the Data directory
            database: ItemDatabase instance
        """
        self.data_dir = Path(data_dir)
        self.images_dir = self.data_dir / "Items" / "Images"
        self.database = database
        self.templates = {}  # item_id -> (template_image, template_gray)

    def load_templates(self):
        """Load all item icon templates from the Images directory."""
        if not self.images_dir.exists():
            raise FileNotFoundError(f"Images directory not found: {self.images_dir}")

        loaded_count = 0
        for png_file in self.images_dir.glob("*.png"):
            item_id = png_file.stem  # filename without extension

            try:
                # Load image
                template = cv2.imread(str(png_file), cv2.IMREAD_COLOR)

                if template is None:
                    print(f"Warning: Could not load image {png_file.name}")
                    continue

                # Resize to standard size if needed
                if template.shape[:2] != (ICON_SIZE[1], ICON_SIZE[0]):
                    template = cv2.resize(template, ICON_SIZE)

                # Convert to grayscale for matching
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                # Store both color and grayscale versions
                self.templates[item_id] = (template, template_gray)
                loaded_count += 1

            except Exception as e:
                print(f"Error loading template {png_file.name}: {e}")

        print(f"Loaded {loaded_count} item icon templates")

    def recognize(self, image: np.ndarray) -> Optional[str]:
        """
        Recognize an item from a captured image using template matching.

        Args:
            image: The captured image (numpy array from OpenCV)

        Returns:
            item_id if recognized with confidence above threshold, None otherwise
        """
        if image is None or len(self.templates) == 0:
            return None

        try:
            # Resize captured image to standard size if needed
            if image.shape[:2] != (ICON_SIZE[1], ICON_SIZE[0]):
                image = cv2.resize(image, ICON_SIZE)

            # Convert to grayscale
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            best_match_id = None
            best_match_score = 0.0

            # Compare against all templates
            for item_id, (template, template_gray) in self.templates.items():
                # Use normalized correlation coefficient matching
                result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)

                if max_val > best_match_score:
                    best_match_score = max_val
                    best_match_id = item_id

            # Return match if above threshold
            if best_match_score >= MATCH_THRESHOLD:
                return best_match_id

            return None

        except Exception as e:
            print(f"Error during recognition: {e}")
            return None

    def recognize_with_score(self, image: np.ndarray) -> Optional[Tuple[str, float]]:
        """
        Recognize an item and return both item_id and confidence score.

        Args:
            image: The captured image (numpy array from OpenCV)

        Returns:
            Tuple of (item_id, confidence_score) if recognized, None otherwise
        """
        if image is None or len(self.templates) == 0:
            return None

        try:
            # Resize captured image to standard size if needed
            if image.shape[:2] != (ICON_SIZE[1], ICON_SIZE[0]):
                image = cv2.resize(image, ICON_SIZE)

            # Convert to grayscale
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            best_match_id = None
            best_match_score = 0.0

            # Compare against all templates
            for item_id, (template, template_gray) in self.templates.items():
                result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)

                if max_val > best_match_score:
                    best_match_score = max_val
                    best_match_id = item_id

            # Return match if above threshold
            if best_match_score >= MATCH_THRESHOLD and best_match_id:
                return (best_match_id, best_match_score)

            return None

        except Exception as e:
            print(f"Error during recognition: {e}")
            return None

    def get_top_matches(self, image: np.ndarray, top_n: int = 5) -> list:
        """
        Get the top N matching items for a captured image.

        Args:
            image: The captured image (numpy array from OpenCV)
            top_n: Number of top matches to return

        Returns:
            List of tuples [(item_id, confidence_score), ...] sorted by score
        """
        if image is None or len(self.templates) == 0:
            return []

        try:
            # Resize captured image to standard size if needed
            if image.shape[:2] != (ICON_SIZE[1], ICON_SIZE[0]):
                image = cv2.resize(image, ICON_SIZE)

            # Convert to grayscale
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            matches = []

            # Compare against all templates
            for item_id, (template, template_gray) in self.templates.items():
                result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                matches.append((item_id, max_val))

            # Sort by score (descending) and return top N
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[:top_n]

        except Exception as e:
            print(f"Error getting top matches: {e}")
            return []
