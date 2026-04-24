import cv2
import yaml
import logging
import time
import sys
import os

# ── Make sure src/ submodules are importable ──────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from camera_handler import CameraHandler
from vision.detector import VehicleDetector
from vision.recognizer import LicensePlateRecognizer
from vision.tracker import CentroidTracker
from logic.entry_exit import EntryExitLogic
from database import db_manager
from utils import drawing

# ── Load configuration ────────────────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
try:
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Error: config not found at {CONFIG_PATH}")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error parsing config: {e}")
    sys.exit(1)

# ── Logging ───────────────────────────────────────────────────────────────────
log_level = getattr(
    logging,
    config.get('logging', {}).get('level', 'INFO').upper(),
    logging.INFO
)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# ── Initialise subsystems ─────────────────────────────────────────────────────
logging.info("=" * 55)
logging.info("  Vehicle Record System — Starting Up")
logging.info("=" * 55)

db_manager.initialize_database()

vision_cfg = config.get('vision', {})
detector = VehicleDetector(
    model_path=vision_cfg.get('detector_model_path', 'models/yolov8n.pt'),
    confidence_threshold=vision_cfg.get('detection_confidence_threshold', 0.4)
)
lpr_enabled = vision_cfg.get('lpr_enabled', False)
recognizer = LicensePlateRecognizer() if lpr_enabled else None
if not lpr_enabled:
    logging.info("LPR is disabled in config (lpr_enabled: false).")

# Per-camera: handler, tracker, entry/exit logic
cameras         = {}
trackers        = {}
entry_exit_logics = {}

for cam_cfg in config.get('cameras', []):
    cam_id = cam_cfg['id']
    cameras[cam_id]           = CameraHandler(cam_cfg['source'])
    trackers[cam_id]          = CentroidTracker(max_disappeared=30)
    entry_exit_logics[cam_id] = EntryExitLogic(cam_cfg)

# ── Counters for HUD ─────────────────────────────────────────────────────────
total_entries = {cam_id: 0 for cam_id in cameras}
total_exits   = {cam_id: 0 for cam_id in cameras}

# ── Main loop ─────────────────────────────────────────────────────────────────
logging.info("Press  Q  in the video window to quit.")
running = True
fps_timer = time.time()
fps_value = 0.0
frame_count = 0

try:
    while running:
        loop_start = time.time()

        for cam_id, camera in cameras.items():
            ret, frame = camera.read_frame()
            if not ret or frame is None:
                continue

            display = frame.copy()

            # 1. Detect vehicles (YOLOv8)
            detections = detector.detect(frame)

            # 2. Update tracker → get {vehicle_id: bbox}
            tracked = trackers[cam_id].update(detections)

            # 3. Draw entry / exit zones
            entry_exit_logics[cam_id].draw_zones(display)

            # 4. Build a lookup: bbox → detection metadata
            #    (for confidence / class labels alongside tracker IDs)
            det_meta = {}  # centroid_key → det dict
            for det in detections:
                bx1, by1, bx2, by2 = det['bbox']
                cx, cy = (bx1 + bx2) // 2, (by1 + by2) // 2
                det_meta[(cx, cy)] = det

            # 5. Process each tracked vehicle
            for vehicle_id, bbox in tracked.items():
                x1, y1, x2, y2 = bbox
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                plate_text = None
                confidence = None
                veh_class  = None

                # Try to match with a detection for meta info
                best_key = None
                best_dist = float('inf')
                for key in det_meta:
                    d = ((key[0] - cx) ** 2 + (key[1] - cy) ** 2) ** 0.5
                    if d < best_dist:
                        best_dist = d
                        best_key = key
                if best_key and best_dist < 50:
                    meta = det_meta[best_key]
                    confidence = meta.get('confidence')
                    veh_class  = meta.get('class')

                    # 5a. License plate recognition (if enabled)
                    if recognizer:
                        vehicle_crop = frame[y1:y2, x1:x2]
                        if vehicle_crop.size > 0:
                            plate_text = recognizer.recognize(vehicle_crop)

                # 5b. Entry / Exit logic (uses stable tracker vehicle_id)
                event = entry_exit_logics[cam_id].determine_event(
                    str(vehicle_id), bbox
                )

                # 5c. Log to DB on entry/exit event
                if event:
                    db_manager.log_vehicle_event(
                        cam_id,
                        event,
                        license_plate=plate_text
                    )
                    if event == 'ENTRY':
                        total_entries[cam_id] += 1
                        logging.info(
                            f"[{cam_id}] ENTRY  — ID:{vehicle_id}  "
                            f"Plate:{plate_text or 'N/A'}"
                        )
                    elif event == 'EXIT':
                        total_exits[cam_id] += 1
                        logging.info(
                            f"[{cam_id}] EXIT   — ID:{vehicle_id}  "
                            f"Plate:{plate_text or 'N/A'}"
                        )

                # 5d. Draw on display frame
                drawing.draw_detection(
                    display, bbox,
                    vehicle_id=vehicle_id,
                    plate_text=plate_text,
                    confidence=confidence,
                    vehicle_class=veh_class
                )

            # 6. Stats HUD
            drawing.draw_stats(
                display,
                vehicle_count=len(tracked),
                entry_count=total_entries[cam_id],
                exit_count=total_exits[cam_id],
                fps=fps_value
            )

            # 7. Show frame
            cv2.imshow(f"Vehicle Record System — {cam_id}", display)
            frame_count += 1

        # ── FPS calculation ──
        elapsed = time.time() - loop_start
        if elapsed > 0:
            fps_value = 0.8 * fps_value + 0.2 * (1.0 / elapsed)  # smoothed

        # ── Keyboard input ──
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            logging.info("Quit key pressed. Shutting down...")
            running = False

except KeyboardInterrupt:
    logging.info("KeyboardInterrupt received. Shutting down...")

finally:
    logging.info("Releasing resources...")
    for camera in cameras.values():
        camera.release()
    cv2.destroyAllWindows()

    # ── Full DB Report (shown automatically after pressing Q) ─────────────
    import sqlite3 as _sqlite3

    SEP = "=" * 60

    print("\n" + SEP)
    print("  📋  VEHICLE RECORD SYSTEM — SESSION REPORT")
    print(SEP)
    print(f"  Total frames processed : {frame_count}")

    for cam_id in cameras:
        print(f"\n  Camera  : {cam_id}")
        print(f"  ENTRY events (this run) : {total_entries[cam_id]}")
        print(f"  EXIT  events (this run) : {total_exits[cam_id]}")

    # Pull full counts from DB
    try:
        _conn = _sqlite3.connect(
            config.get('database', {}).get('path', 'vehicle_log.db')
        )
        _conn.row_factory = _sqlite3.Row
        _cur = _conn.cursor()

        _cur.execute("SELECT COUNT(*) FROM vehicle_logs")
        db_total = _cur.fetchone()[0]

        _cur.execute("SELECT COUNT(*) FROM vehicle_logs WHERE event_type='ENTRY'")
        db_entries = _cur.fetchone()[0]

        _cur.execute("SELECT COUNT(*) FROM vehicle_logs WHERE event_type='EXIT'")
        db_exits = _cur.fetchone()[0]

        print(f"\n  ── Database totals (all time) ──")
        print(f"  Total logged events : {db_total}")
        print(f"  Total ENTRYs        : {db_entries}")
        print(f"  Total EXITs         : {db_exits}")

        # Last 10 events
        _cur.execute(
            "SELECT id, timestamp, camera_id, event_type, license_plate "
            "FROM vehicle_logs ORDER BY timestamp DESC LIMIT 10"
        )
        rows = _cur.fetchall()
        print(f"\n  ── Last 10 logged events ──")
        print(f"  {'ID':<5} {'Timestamp':<26} {'Camera':<20} {'Event':<8} {'Plate'}")
        print("  " + "-" * 56)
        for r in rows:
            plate = r['license_plate'] or 'N/A'
            print(
                f"  {r['id']:<5} {r['timestamp']:<26} "
                f"{r['camera_id']:<20} {r['event_type']:<8} {plate}"
            )
        _conn.close()
    except Exception as _e:
        print(f"  [DB read error: {_e}]")

    print("\n" + SEP + "\n")