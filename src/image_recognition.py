"""Image recognition module for identifying items."""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
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
        self.templates = {}  # item_id -> (template_image, template_gray, template_hist)

        # Initialize ORB detector for feature-based matching
        self.orb = cv2.ORB_create(nfeatures=500)
        self.template_features = {}  # item_id -> (keypoints, descriptors)

    def load_templates(self):
        """Load all item icon templates from the Images directory."""
        if not self.images_dir.exists():
            raise FileNotFoundError(f"Images directory not found: {self.images_dir}")

        loaded_count = 0
        # Support both .png and .webp formats
        image_files = list(self.images_dir.glob("*.png")) + list(self.images_dir.glob("*.webp"))

        for image_file in image_files:
            item_id = image_file.stem  # filename without extension

            try:
                # Load image - use PIL for .webp files, OpenCV for others
                if image_file.suffix.lower() == '.webp':
                    # Use PIL to load WebP files
                    pil_image = Image.open(str(image_file)).convert('RGB')
                    # Convert PIL image to OpenCV format (RGB -> BGR)
                    template = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                else:
                    # Use OpenCV for PNG and other formats
                    template = cv2.imread(str(image_file), cv2.IMREAD_COLOR)

                if template is None:
                    print(f"Warning: Could not load image {image_file.name}")
                    continue

                # Resize to standard size if needed
                if template.shape[:2] != (ICON_SIZE[1], ICON_SIZE[0]):
                    template = cv2.resize(template, ICON_SIZE)

                # Convert to grayscale for matching
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                # Apply histogram equalization for better lighting normalization
                template_gray_eq = cv2.equalizeHist(template_gray)

                # Calculate histogram for color-based matching
                hist = cv2.calcHist([template], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                hist = cv2.normalize(hist, hist).flatten()

                # Extract ORB features
                keypoints, descriptors = self.orb.detectAndCompute(template_gray_eq, None)

                # Store all matching data
                self.templates[item_id] = (template, template_gray, template_gray_eq, hist)
                if descriptors is not None:
                    self.template_features[item_id] = (keypoints, descriptors)

                loaded_count += 1

            except Exception as e:
                print(f"Error loading template {image_file.name}: {e}")

        print(f"Loaded {loaded_count} item icon templates")

    def _calculate_match_score(self, image_gray, image_gray_eq, image_hist,
                                template_gray, template_gray_eq, template_hist,
                                item_id) -> float:
        """
        Calculate comprehensive match score using multiple methods.

        Args:
            image_gray: Grayscale input image
            image_gray_eq: Histogram-equalized grayscale input
            image_hist: Color histogram of input
            template_gray: Grayscale template
            template_gray_eq: Histogram-equalized template
            template_hist: Color histogram of template
            item_id: Template item ID for feature matching

        Returns:
            Combined match score (0.0-1.0)
        """
        scores = []
        weights = []

        # 1. Template matching with normalized correlation (original method)
        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, score1, _, _ = cv2.minMaxLoc(result)
        scores.append(score1)
        weights.append(0.25)

        # 2. Template matching with correlation coefficient
        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCORR_NORMED)
        _, score2, _, _ = cv2.minMaxLoc(result)
        scores.append(score2)
        weights.append(0.15)

        # 3. Template matching on equalized images (lighting invariant)
        result = cv2.matchTemplate(image_gray_eq, template_gray_eq, cv2.TM_CCOEFF_NORMED)
        _, score3, _, _ = cv2.minMaxLoc(result)
        scores.append(score3)
        weights.append(0.30)

        # 4. Histogram comparison (color similarity)
        hist_score = cv2.compareHist(image_hist, template_hist, cv2.HISTCMP_CORREL)
        scores.append(hist_score)
        weights.append(0.15)

        # 5. Feature-based matching with ORB
        if item_id in self.template_features:
            try:
                kp_img, desc_img = self.orb.detectAndCompute(image_gray_eq, None)
                kp_tpl, desc_tpl = self.template_features[item_id]

                if desc_img is not None and desc_tpl is not None and len(desc_img) > 0 and len(kp_img) > 0:
                    # Use BFMatcher for matching
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(desc_img, desc_tpl)

                    # Calculate feature match score based on good matches
                    if len(matches) > 0:
                        # Sort by distance and take best matches
                        matches = sorted(matches, key=lambda x: x.distance)
                        good_matches = [m for m in matches if m.distance < 50]

                        # Score based on ratio of good matches
                        feature_score = min(1.0, len(good_matches) / max(10, len(kp_tpl) * 0.3))
                        scores.append(feature_score)
                        weights.append(0.15)
                    else:
                        scores.append(0.0)
                        weights.append(0.15)
                else:
                    scores.append(0.0)
                    weights.append(0.15)
            except Exception:
                scores.append(0.0)
                weights.append(0.15)
        else:
            scores.append(0.0)
            weights.append(0.15)

        # Calculate weighted average
        total_weight = sum(weights)
        if total_weight > 0:
            final_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        else:
            final_score = 0.0

        return max(0.0, min(1.0, final_score))

    def recognize(self, image: np.ndarray, cancel_event=None) -> Optional[str]:
        """
        Recognize an item from a captured image using advanced template matching.

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

            # Prepare image for matching
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_gray_eq = cv2.equalizeHist(image_gray)
            image_hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            image_hist = cv2.normalize(image_hist, image_hist).flatten()

            best_match_id = None
            best_match_score = 0.0

            # Compare against all templates using comprehensive scoring
            for item_id, (template, template_gray, template_gray_eq, template_hist) in self.templates.items():
                if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                    return None
                score = self._calculate_match_score(
                    image_gray, image_gray_eq, image_hist,
                    template_gray, template_gray_eq, template_hist,
                    item_id
                )

                if score > best_match_score:
                    best_match_score = score
                    best_match_id = item_id

            # Return match if above threshold
            if best_match_score >= MATCH_THRESHOLD:
                return best_match_id

            return None

        except Exception as e:
            print(f"Error during recognition: {e}")
            return None

    def recognize_with_score(self, image: np.ndarray, cancel_event=None) -> Optional[Tuple[str, float]]:
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

            # Prepare image for matching
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_gray_eq = cv2.equalizeHist(image_gray)
            image_hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            image_hist = cv2.normalize(image_hist, image_hist).flatten()

            best_match_id = None
            best_match_score = 0.0

            # Compare against all templates using comprehensive scoring
            for item_id, (template, template_gray, template_gray_eq, template_hist) in self.templates.items():
                if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                    return None
                score = self._calculate_match_score(
                    image_gray, image_gray_eq, image_hist,
                    template_gray, template_gray_eq, template_hist,
                    item_id
                )

                if score > best_match_score:
                    best_match_score = score
                    best_match_id = item_id

            # Return match if above threshold
            if best_match_score >= MATCH_THRESHOLD and best_match_id:
                return (best_match_id, best_match_score)

            return None

        except Exception as e:
            print(f"Error during recognition: {e}")
            return None

    def get_top_matches(self, image: np.ndarray, top_n: int = 5, cancel_event=None) -> list:
        """
        Get the top N matching items for a captured image using advanced matching.

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

            # Prepare image for matching
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_gray_eq = cv2.equalizeHist(image_gray)
            image_hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            image_hist = cv2.normalize(image_hist, image_hist).flatten()

            matches = []

            # Compare against all templates using comprehensive scoring
            for item_id, (template, template_gray, template_gray_eq, template_hist) in self.templates.items():
                if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                    return []
                score = self._calculate_match_score(
                    image_gray, image_gray_eq, image_hist,
                    template_gray, template_gray_eq, template_hist,
                    item_id
                )
                matches.append((item_id, score))

            # Sort by score (descending) and return top N
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[:top_n]

        except Exception as e:
            print(f"Error getting top matches: {e}")
            return []
