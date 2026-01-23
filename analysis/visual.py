import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class VisualAnalysis:
    def __init__(self, logos_path: str = "resources/logos", threshold: float = 0.8):
        self.logos_path = logos_path
        self.threshold = threshold
        # Load templates in memory? Or load on demand.
        # Since we might have few logos, loading on demand is safer for now or we preload.
        # Let's preload if possible, but folder might be empty initially.
        os.makedirs(self.logos_path, exist_ok=True)

    def analyze_screenshot(self, screenshot_bytes: bytes):
        """Checks the screenshot against known logos."""
        if not screenshot_bytes:
            return {"brand_detected": None, "confidence": 0}

        # Convert bytes to cv2 image
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        img_scene = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_scene is None:
            return {"error": "failed_to_decode_screenshot"}
        
        # Convert to grayscale for template matching
        gray_scene = cv2.cvtColor(img_scene, cv2.COLOR_BGR2GRAY)

        # Iterate over logos
        best_match = None
        max_val_found = 0
        detected = []

        if not os.path.exists(self.logos_path):
             return {"brand_detected": None, "confidence": 0, "note": "logos_dir_missing"}

        for logo_file in os.listdir(self.logos_path):
            if logo_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                logo_path = os.path.join(self.logos_path, logo_file)
                template = cv2.imread(logo_path, 0) # Read as grayscale
                if template is None:
                    continue
                
                # Check sizes: Template must be smaller than scene
                if template.shape[0] > gray_scene.shape[0] or template.shape[1] > gray_scene.shape[1]:
                    logger.debug(f"Logo {logo_file} is larger than screenshot, skipping.")
                    continue

                # Template Matching
                res = cv2.matchTemplate(gray_scene, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                if max_val >= self.threshold:
                    detected.append({
                        "brand": os.path.splitext(logo_file)[0],
                        "confidence": float(max_val)
                    })
                    if max_val > max_val_found:
                        max_val_found = max_val
                        best_match = os.path.splitext(logo_file)[0]

        return {
            "brand_detected": best_match,
            "confidence": float(max_val_found),
            "all_matches": detected
        }
