import cv2


# Color palette
COLOR_VEHICLE = (0, 200, 255)      # amber – bounding box
COLOR_PLATE   = (50, 255, 50)      # green – plate text
COLOR_ID      = (255, 255, 255)    # white – tracker ID
COLOR_CONF    = (180, 180, 180)    # grey  – confidence
FONT          = cv2.FONT_HERSHEY_SIMPLEX


def draw_detection(frame, bbox, vehicle_id=None, plate_text=None,
                   confidence=None, vehicle_class=None):
    """
    Draws a bounding box, tracker ID, confidence, class label, and plate text
    on the frame.

    Args:
        frame:         BGR image (NumPy array) – modified in-place.
        bbox:          [x1, y1, x2, y2]
        vehicle_id:    Tracker-assigned integer ID (or None).
        plate_text:    Recognized plate string (or None).
        confidence:    Detection confidence float (or None).
        vehicle_class: Class label string, e.g. 'car' (or None).
    """
    x1, y1, x2, y2 = bbox

    # --- Bounding box ---
    cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_VEHICLE, 2)

    # --- Top label: ID + class + confidence ---
    parts = []
    if vehicle_id is not None:
        parts.append(f"#{vehicle_id}")
    if vehicle_class:
        parts.append(vehicle_class)
    if confidence is not None:
        parts.append(f"{confidence:.0%}")

    label = "  ".join(parts) if parts else "vehicle"

    (lw, lh), baseline = cv2.getTextSize(label, FONT, 0.5, 1)
    label_y = max(y1 - 6, lh + 4)
    cv2.rectangle(frame,
                  (x1, label_y - lh - baseline - 2),
                  (x1 + lw + 4, label_y),
                  COLOR_VEHICLE, cv2.FILLED)
    cv2.putText(frame, label, (x1 + 2, label_y - baseline),
                FONT, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # --- Bottom label: plate text ---
    if plate_text:
        plate_label = f"Plate: {plate_text}"
        (pw, ph), pb = cv2.getTextSize(plate_label, FONT, 0.5, 1)
        plate_y = min(y2 + ph + 6, frame.shape[0] - 2)
        cv2.rectangle(frame,
                      (x1, plate_y - ph - pb - 2),
                      (x1 + pw + 4, plate_y),
                      COLOR_PLATE, cv2.FILLED)
        cv2.putText(frame, plate_label, (x1 + 2, plate_y - pb),
                    FONT, 0.5, (0, 0, 0), 1, cv2.LINE_AA)


def draw_stats(frame, vehicle_count, entry_count, exit_count, fps=None):
    """
    Draws a semi-transparent stats overlay in the top-left corner.
    """
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (220, 90), (20, 20, 20), cv2.FILLED)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    lines = [
        f"Vehicles: {vehicle_count}",
        f"Entries : {entry_count}",
        f"Exits   : {exit_count}",
    ]
    if fps is not None:
        lines.append(f"FPS     : {fps:.1f}")

    for i, line in enumerate(lines):
        cv2.putText(frame, line, (8, 18 + i * 18),
                    FONT, 0.5, COLOR_ID, 1, cv2.LINE_AA)