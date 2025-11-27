"""Image recognition module for identifying items."""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image
from src.config import MATCH_THRESHOLD, MATCH_THRESHOLD_LOW, ICON_SIZE


class ItemRecognizer:
    """Recognizes items from captured images using advanced multi-method template matching."""

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

        # Initialize feature detectors for advanced matching
        self.orb = cv2.ORB_create(nfeatures=500)

        # Try to initialize SIFT (more accurate than ORB, but requires opencv-contrib-python)
        try:
            self.sift = cv2.SIFT_create(nfeatures=500)
            self.use_sift = True
            print("SIFT detector initialized successfully")
        except Exception as e:
            self.use_sift = False
            print(f"SIFT not available (requires opencv-contrib-python): {e}")

        self.template_features = {}  # item_id -> (orb_desc, sift_desc)

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
                orb_kp, orb_desc = self.orb.detectAndCompute(template_gray_eq, None)

                # Extract SIFT features if available
                sift_kp, sift_desc = None, None
                if self.use_sift:
                    try:
                        sift_kp, sift_desc = self.sift.detectAndCompute(template_gray_eq, None)
                    except Exception:
                        pass

                # Store all matching data
                self.templates[item_id] = (template, template_gray, template_gray_eq, hist)
                if orb_desc is not None or sift_desc is not None:
                    self.template_features[item_id] = {
                        'orb': (orb_kp, orb_desc),
                        'sift': (sift_kp, sift_desc)
                    }

                loaded_count += 1

            except Exception as e:
                print(f"Error loading template {image_file.name}: {e}")

        print(f"Loaded {loaded_count} item icon templates")

    def _calculate_match_score(self, image_gray, image_gray_eq, image_hist,
                                template_gray, template_gray_eq, template_hist,
                                item_id, orb_features=None, sift_features=None) -> Tuple[float, dict]:
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
            orb_features: Pre-computed ORB features for input image (optional)
            sift_features: Pre-computed SIFT features for input image (optional)

        Returns:
            Tuple of (combined match score, detailed scores dict)
        """
        scores = []
        weights = []
        score_details = {}

        # 1. Quick histogram pre-filter to skip obviously wrong matches
        hist_score = cv2.compareHist(image_hist, template_hist, cv2.HISTCMP_CORREL)
        score_details['histogram'] = hist_score

        # If histogram similarity is too low, skip expensive computations
        if hist_score < 0.3:
            return 0.0, score_details

        # 2. Template matching with normalized correlation
        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, score1, _, _ = cv2.minMaxLoc(result)
        scores.append(score1)
        weights.append(0.20)
        score_details['template_ccoeff'] = score1

        # 3. Template matching with correlation coefficient
        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCORR_NORMED)
        _, score2, _, _ = cv2.minMaxLoc(result)
        scores.append(score2)
        weights.append(0.10)
        score_details['template_ccorr'] = score2

        # 4. Template matching on equalized images (lighting invariant)
        result = cv2.matchTemplate(image_gray_eq, template_gray_eq, cv2.TM_CCOEFF_NORMED)
        _, score3, _, _ = cv2.minMaxLoc(result)
        scores.append(score3)
        weights.append(0.25)
        score_details['template_equalized'] = score3

        # 5. Histogram comparison (already computed)
        scores.append(hist_score)
        weights.append(0.15)

        # 6. ORB feature matching
        orb_score = 0.0
        if item_id in self.template_features and orb_features is not None:
            try:
                kp_img, desc_img = orb_features
                template_features = self.template_features[item_id]
                kp_tpl, desc_tpl = template_features['orb']

                if desc_img is not None and desc_tpl is not None and len(desc_img) > 0:
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(desc_img, desc_tpl)

                    if len(matches) > 0:
                        matches = sorted(matches, key=lambda x: x.distance)
                        good_matches = [m for m in matches if m.distance < 50]
                        orb_score = min(1.0, len(good_matches) / max(10, len(kp_tpl) * 0.3))
            except Exception:
                pass

        scores.append(orb_score)
        weights.append(0.15)
        score_details['orb_features'] = orb_score

        # 7. SIFT feature matching (more accurate than ORB)
        sift_score = 0.0
        if self.use_sift and item_id in self.template_features and sift_features is not None:
            try:
                kp_img, desc_img = sift_features
                template_features = self.template_features[item_id]
                kp_tpl, desc_tpl = template_features['sift']

                if desc_img is not None and desc_tpl is not None and len(desc_img) > 0:
                    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
                    matches = bf.match(desc_img, desc_tpl)

                    if len(matches) > 0:
                        matches = sorted(matches, key=lambda x: x.distance)
                        # SIFT uses different distance metric
                        good_matches = [m for m in matches if m.distance < 200]
                        sift_score = min(1.0, len(good_matches) / max(10, len(kp_tpl) * 0.3))
            except Exception:
                pass

        scores.append(sift_score)
        weights.append(0.15)
        score_details['sift_features'] = sift_score

        # Calculate weighted average
        total_weight = sum(weights)
        if total_weight > 0:
            final_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        else:
            final_score = 0.0

        score_details['final'] = final_score
        return max(0.0, min(1.0, final_score)), score_details

    def _remove_white_background(self, image: np.ndarray) -> np.ndarray:
        """
        Remove white/light border from captured screenshot by cropping to content.

        This helps when icons are smaller than expected and have white/light borders.
        The function detects white edges and crops them away, then scales the icon
        back to the original size.

        Args:
            image: Input image (BGR format)

        Returns:
            Processed image with white borders removed and icon scaled to original size
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # Check if edges are light (white/light gray background)
            # Sample pixels from all 4 edges (use larger sample area)
            edge_width = 5
            top_edge = np.mean(gray[0:edge_width, :])
            bottom_edge = np.mean(gray[-edge_width:, :])
            left_edge = np.mean(gray[:, 0:edge_width])
            right_edge = np.mean(gray[:, -edge_width:])

            # Lower threshold to catch light gray backgrounds (>200 instead of >230)
            light_threshold = 200
            light_edges = sum([
                top_edge > light_threshold,
                bottom_edge > light_threshold,
                left_edge > light_threshold,
                right_edge > light_threshold
            ])

            # If less than 2 edges are light, no white background detected
            if light_edges < 2:
                return image

            # Find non-white content by thresholding
            # Lower threshold to catch more light backgrounds (180 instead of 230)
            _, mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

            # Apply morphological operations to clean up the mask
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Find contours to get the main content area
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                return image

            # Find the largest contour (assumed to be the icon)
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, cw, ch = cv2.boundingRect(largest_contour)

            # Calculate content dimensions
            content_width = cw
            content_height = ch

            # If content takes up most of the image (>85%), no need to crop
            if content_width >= w * 0.85 and content_height >= h * 0.85:
                return image

            # If content is too small (<15% of image), might be noise - don't crop
            if content_width < w * 0.15 or content_height < h * 0.15:
                return image

            # Add padding to the crop area
            padding = 3
            crop_left = max(0, x - padding)
            crop_right = min(w, x + cw + padding)
            crop_top = max(0, y - padding)
            crop_bottom = min(h, y + ch + padding)

            # Crop to content
            cropped = image[crop_top:crop_bottom, crop_left:crop_right]

            # Resize back to original dimensions
            # This ensures the icon fills the frame properly for recognition
            result = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)

            print(f"Background removal: cropped from {w}x{h} to {crop_right-crop_left}x{crop_bottom-crop_top}, resized back to {w}x{h}")

            return result

        except Exception as e:
            print(f"Warning: Error removing white background: {e}")
            return image  # Return original on error

    def recognize(self, image: np.ndarray, cancel_event=None) -> Optional[str]:
        """
        Recognize an item from a captured image using advanced template matching.

        Args:
            image: The captured image (numpy array from OpenCV)
            cancel_event: Event to signal cancellation

        Returns:
            item_id if recognized with confidence above threshold, None otherwise
        """
        if image is None or len(self.templates) == 0:
            return None

        try:
            # Remove white background if present
            image = self._remove_white_background(image)

            # Resize captured image to standard size if needed
            if image.shape[:2] != (ICON_SIZE[1], ICON_SIZE[0]):
                image = cv2.resize(image, ICON_SIZE)

            # Prepare image for matching (computed once)
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_gray_eq = cv2.equalizeHist(image_gray)
            image_hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            image_hist = cv2.normalize(image_hist, image_hist).flatten()

            # Pre-compute features once for all comparisons
            orb_features = self.orb.detectAndCompute(image_gray_eq, None)
            sift_features = None
            if self.use_sift:
                try:
                    sift_features = self.sift.detectAndCompute(image_gray_eq, None)
                except Exception:
                    pass

            best_match_id = None
            best_match_score = 0.0

            # Compare against all templates using comprehensive scoring
            for item_id, (template, template_gray, template_gray_eq, template_hist) in self.templates.items():
                if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                    return None

                score, _ = self._calculate_match_score(
                    image_gray, image_gray_eq, image_hist,
                    template_gray, template_gray_eq, template_hist,
                    item_id, orb_features, sift_features
                )

                if score > best_match_score:
                    best_match_score = score
                    best_match_id = item_id

            # Return match if above threshold
            if best_match_score >= MATCH_THRESHOLD:
                print(f"Recognized: {best_match_id} (confidence: {best_match_score:.3f})")
                return best_match_id
            else:
                print(f"No match above threshold. Best: {best_match_id} ({best_match_score:.3f})")

            return None

        except Exception as e:
            print(f"Error during recognition: {e}")
            import traceback
            traceback.print_exc()
            return None

    def recognize_with_score(self, image: np.ndarray, cancel_event=None) -> Optional[Tuple[str, float, dict]]:
        """
        Recognize an item and return item_id, confidence score, and detailed scores.

        Args:
            image: The captured image (numpy array from OpenCV)
            cancel_event: Event to signal cancellation

        Returns:
            Tuple of (item_id, confidence_score, score_details) if recognized, None otherwise
        """
        if image is None or len(self.templates) == 0:
            return None

        try:
            # Remove white background if present
            image = self._remove_white_background(image)

            # Resize captured image to standard size if needed
            if image.shape[:2] != (ICON_SIZE[1], ICON_SIZE[0]):
                image = cv2.resize(image, ICON_SIZE)

            # Prepare image for matching (computed once)
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_gray_eq = cv2.equalizeHist(image_gray)
            image_hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            image_hist = cv2.normalize(image_hist, image_hist).flatten()

            # Pre-compute features once
            orb_features = self.orb.detectAndCompute(image_gray_eq, None)
            sift_features = None
            if self.use_sift:
                try:
                    sift_features = self.sift.detectAndCompute(image_gray_eq, None)
                except Exception:
                    pass

            best_match_id = None
            best_match_score = 0.0
            best_score_details = {}

            # Compare against all templates
            for item_id, (template, template_gray, template_gray_eq, template_hist) in self.templates.items():
                if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                    return None

                score, details = self._calculate_match_score(
                    image_gray, image_gray_eq, image_hist,
                    template_gray, template_gray_eq, template_hist,
                    item_id, orb_features, sift_features
                )

                if score > best_match_score:
                    best_match_score = score
                    best_match_id = item_id
                    best_score_details = details

            # Return match if above threshold
            if best_match_score >= MATCH_THRESHOLD and best_match_id:
                return (best_match_id, best_match_score, best_score_details)

            return None

        except Exception as e:
            print(f"Error during recognition: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_top_matches(self, image: np.ndarray, top_n: int = 5, cancel_event=None) -> List[Tuple[str, float, dict]]:
        """
        Get the top N matching items for a captured image with detailed scores.

        Args:
            image: The captured image (numpy array from OpenCV)
            top_n: Number of top matches to return
            cancel_event: Event to signal cancellation

        Returns:
            List of tuples [(item_id, confidence_score, score_details), ...] sorted by score
        """
        if image is None or len(self.templates) == 0:
            return []

        try:
            # Remove white background if present
            image = self._remove_white_background(image)

            # Resize captured image to standard size if needed
            if image.shape[:2] != (ICON_SIZE[1], ICON_SIZE[0]):
                image = cv2.resize(image, ICON_SIZE)

            # Prepare image for matching (computed once)
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_gray_eq = cv2.equalizeHist(image_gray)
            image_hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            image_hist = cv2.normalize(image_hist, image_hist).flatten()

            # Pre-compute features once
            orb_features = self.orb.detectAndCompute(image_gray_eq, None)
            sift_features = None
            if self.use_sift:
                try:
                    sift_features = self.sift.detectAndCompute(image_gray_eq, None)
                except Exception:
                    pass

            matches = []

            # Compare against all templates
            for item_id, (template, template_gray, template_gray_eq, template_hist) in self.templates.items():
                if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                    return []

                score, details = self._calculate_match_score(
                    image_gray, image_gray_eq, image_hist,
                    template_gray, template_gray_eq, template_hist,
                    item_id, orb_features, sift_features
                )
                matches.append((item_id, score, details))

            # Sort by score (descending) and return top N
            matches.sort(key=lambda x: x[1], reverse=True)

            # Print top matches for debugging
            print(f"\nTop {min(top_n, len(matches))} matches:")
            for i, (item_id, score, details) in enumerate(matches[:top_n], 1):
                print(f"  {i}. {item_id}: {score:.3f}")
                if details:
                    print(f"     Details: hist={details.get('histogram', 0):.2f}, "
                          f"eq={details.get('template_equalized', 0):.2f}, "
                          f"orb={details.get('orb_features', 0):.2f}, "
                          f"sift={details.get('sift_features', 0):.2f}")

            return matches[:top_n]

        except Exception as e:
            print(f"Error getting top matches: {e}")
            import traceback
            traceback.print_exc()
            return []

    def recognize_adaptive(self, image: np.ndarray, cancel_event=None) -> Optional[dict]:
        """
        Recognize an item with adaptive threshold - returns confident or possible matches.

        Args:
            image: The captured image (numpy array from OpenCV)
            cancel_event: Event to signal cancellation

        Returns:
            Dict with 'status' ('confident', 'possible', 'failed'), 'item_id', 'confidence', 'alternatives'
        """
        if image is None or len(self.templates) == 0:
            return {'status': 'failed', 'item_id': None, 'confidence': 0.0, 'alternatives': []}

        try:
            # Get top 3 matches
            top_matches = self.get_top_matches(image, top_n=3, cancel_event=cancel_event)

            if not top_matches:
                return {'status': 'failed', 'item_id': None, 'confidence': 0.0, 'alternatives': []}

            best_match_id, best_score, best_details = top_matches[0]

            # Prepare result
            result = {
                'item_id': best_match_id,
                'confidence': best_score,
                'score_details': best_details,
                'alternatives': [(item_id, score) for item_id, score, _ in top_matches[1:3]]
            }

            # Determine status based on adaptive thresholds
            if best_score >= MATCH_THRESHOLD:
                result['status'] = 'confident'
                print(f"✓ Confident match: {best_match_id} ({best_score:.1%})")
            elif best_score >= MATCH_THRESHOLD_LOW:
                result['status'] = 'possible'
                print(f"? Possible match: {best_match_id} ({best_score:.1%})")
                if len(result['alternatives']) > 0:
                    alt_text = ', '.join([f"{id} ({s:.1%})" for id, s in result['alternatives']])
                    print(f"  Alternatives: {alt_text}")
            else:
                result['status'] = 'failed'
                print(f"✗ No good match. Best: {best_match_id} ({best_score:.1%})")

            return result

        except Exception as e:
            print(f"Error during adaptive recognition: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'failed', 'item_id': None, 'confidence': 0.0, 'alternatives': []}
