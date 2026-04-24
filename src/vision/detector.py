import cv2
import logging
from ultralytics import YOLO


# COCO dataset vehicle class IDs (car, motorcycle, bus, truck)
VEHICLE_CLASS_IDS = {2, 3, 5, 7}
VEHICLE_CLASS_NAMES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


class VehicleDetector:
    def __init__(self, model_path, confidence_threshold=0.4):
        self.confidence_threshold = confidence_threshold
        self.model_path = model_path
        self.model = None
        try:
            # Ultralytics will auto-download yolov8n.pt if not present locally
            self.model = YOLO(model_path)
            logging.info(f"YOLOv8 model loaded from '{model_path}'")
        except Exception as e:
            logging.error(f"Failed to load detection model: {e}")
            self.model = None

    def detect(self, frame):
        """
        Detects vehicles in a given frame using YOLOv8.

        Args:
            frame: The input image frame (NumPy array).

        Returns:
            A list of detected vehicles:
            [{'bbox': [x1, y1, x2, y2], 'confidence': float, 'class': str}, ...]
        """
        if self.model is None:
            logging.warning("Detection model not loaded. Skipping frame.")
            return []

        detections = []
        try:
            results = self.model(frame, verbose=False)
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])

                    if class_id in VEHICLE_CLASS_IDS and confidence >= self.confidence_threshold:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        detections.append({
                            'bbox': [x1, y1, x2, y2],
                            'confidence': confidence,
                            'class': VEHICLE_CLASS_NAMES.get(class_id, "vehicle")
                        })
        except Exception as e:
            logging.error(f"Error during detection inference: {e}")

        logging.debug(f"Detected {len(detections)} vehicles.")
        return detections