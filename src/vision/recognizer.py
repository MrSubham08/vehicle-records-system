import cv2
import logging
import easyocr
import numpy as np


class LicensePlateRecognizer:
    def __init__(self):
        self.reader = None
        try:
            # Initialize EasyOCR with English language
            # gpu=False forces CPU mode (safe default; set True if CUDA GPU is available)
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logging.info("EasyOCR reader initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize EasyOCR reader: {e}")
            self.reader = None

    def _preprocess(self, image):
        """Prepares the vehicle crop for better OCR accuracy."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Upscale small crops so OCR has more pixels to work with
        if gray.shape[0] < 100 or gray.shape[1] < 200:
            gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        # Denoise then threshold
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def recognize(self, vehicle_image):
        """
        Attempts to read a license plate from a cropped vehicle image.

        Args:
            vehicle_image: Cropped vehicle image (NumPy BGR array).

        Returns:
            Recognized plate text (str) or None if unreadable.
        """
        if self.reader is None:
            logging.warning("OCR reader not initialized. Cannot recognize plate.")
            return None

        if vehicle_image is None or vehicle_image.size == 0:
            return None

        plate_text = None
        try:
            processed = self._preprocess(vehicle_image)
            results = self.reader.readtext(processed)

            if results:
                # Pick the result with highest confidence
                best = max(results, key=lambda item: item[2])
                raw_text = best[1]
                confidence = best[2]

                # Clean: keep only alphanumeric characters, uppercase
                cleaned = "".join(filter(str.isalnum, raw_text)).upper()

                # Basic validity: 4–10 chars, confidence above 30%
                if 4 <= len(cleaned) <= 10 and confidence >= 0.30:
                    plate_text = cleaned
                    logging.debug(
                        f"Plate recognized: '{plate_text}' (conf: {confidence:.2f})"
                    )
        except Exception as e:
            logging.debug(f"OCR error on crop: {e}")

        return plate_text