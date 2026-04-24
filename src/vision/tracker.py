"""
Simple Centroid-Based Vehicle Tracker.

Assigns persistent IDs to vehicles across frames by matching
detected bounding boxes to existing tracked objects using
Euclidean distance between centroids.
"""

import logging
from collections import OrderedDict

import numpy as np


class CentroidTracker:
    def __init__(self, max_disappeared=30):
        """
        Args:
            max_disappeared: Number of consecutive frames a vehicle can be
                             missing before being deregistered.
        """
        self.next_object_id = 0
        self.objects = OrderedDict()        # {id: centroid (cx, cy)}
        self.bboxes = OrderedDict()         # {id: [x1, y1, x2, y2]}
        self.disappeared = OrderedDict()    # {id: frame_count_since_last_seen}
        self.max_disappeared = max_disappeared

    # ------------------------------------------------------------------
    def _centroid(self, bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _register(self, centroid, bbox):
        obj_id = self.next_object_id
        self.objects[obj_id] = centroid
        self.bboxes[obj_id] = bbox
        self.disappeared[obj_id] = 0
        self.next_object_id += 1
        logging.debug(f"Tracker: registered new vehicle ID {obj_id}")
        return obj_id

    def _deregister(self, obj_id):
        del self.objects[obj_id]
        del self.bboxes[obj_id]
        del self.disappeared[obj_id]
        logging.debug(f"Tracker: deregistered vehicle ID {obj_id}")

    # ------------------------------------------------------------------
    def update(self, detections):
        """
        Update tracker with current frame detections.

        Args:
            detections: list of {'bbox': [x1,y1,x2,y2], ...} dicts.

        Returns:
            OrderedDict: {object_id: bbox} for all currently tracked vehicles.
        """
        # --- No detections this frame ---
        if len(detections) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self._deregister(obj_id)
            return self.bboxes

        # --- Build input centroids from detections ---
        input_centroids = []
        input_bboxes = []
        for det in detections:
            bbox = det['bbox']
            input_centroids.append(self._centroid(bbox))
            input_bboxes.append(bbox)

        # --- No existing objects yet: register all ---
        if len(self.objects) == 0:
            for c, b in zip(input_centroids, input_bboxes):
                self._register(c, b)
            return self.bboxes

        # --- Match existing objects to new detections ---
        object_ids = list(self.objects.keys())
        object_centroids = list(self.objects.values())

        # Pairwise Euclidean distances: rows=existing, cols=input
        D = np.linalg.norm(
            np.array(object_centroids)[:, None] - np.array(input_centroids)[None, :],
            axis=2
        )

        # Greedy matching: sort by minimum distance
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if D[row, col] > 80:   # max distance threshold (pixels)
                continue
            obj_id = object_ids[row]
            self.objects[obj_id] = input_centroids[col]
            self.bboxes[obj_id] = input_bboxes[col]
            self.disappeared[obj_id] = 0
            used_rows.add(row)
            used_cols.add(col)

        # Mark unmatched existing objects as disappeared
        for row in set(range(len(object_ids))) - used_rows:
            obj_id = object_ids[row]
            self.disappeared[obj_id] += 1
            if self.disappeared[obj_id] > self.max_disappeared:
                self._deregister(obj_id)

        # Register unmatched new detections
        for col in set(range(len(input_centroids))) - used_cols:
            self._register(input_centroids[col], input_bboxes[col])

        return self.bboxes
