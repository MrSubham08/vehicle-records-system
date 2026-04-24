import cv2
import logging
import time
import os

class CameraHandler:
    def __init__(self, source):
        self.source = source
        self.cap = None
        # Detect if source is a file (for looping support)
        self.is_file = isinstance(source, str) and os.path.isfile(source)
        self.connect()

    def connect(self):
        """Establishes connection to the video source."""
        logging.info(f"Attempting to connect to camera source: {self.source}")
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            logging.error(f"Failed to open video source: {self.source}")
            self.cap = None
        else:
            logging.info(f"Successfully connected to video source: {self.source}")

    def read_frame(self):
        """Reads a single frame from the video source."""
        if self.cap is None or not self.cap.isOpened():
            if not self.is_file:
                logging.warning(f"Camera source {self.source} not available. Attempting reconnect.")
                time.sleep(2)
                self.connect()
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            if self.is_file:
                # Loop the video file back to the beginning
                logging.info(f"End of video file '{self.source}'. Looping from start.")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    logging.error(f"Could not loop video file: {self.source}")
                    return False, None
            else:
                logging.warning(f"Failed to read frame from source: {self.source}. End of stream or error?")
                return False, None
        return ret, frame

    def release(self):
        """Releases the video capture object."""
        if self.cap is not None:
            logging.info(f"Releasing video source: {self.source}")
            self.cap.release()
            self.cap = None

    def __del__(self):
        self.release()  # Ensure release on object deletion