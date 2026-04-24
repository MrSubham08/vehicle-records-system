import logging
import cv2
def check_zone_crossing(bbox, zone):
    """Checks if the center of a bounding box is inside a zone."""
    if not zone or len(zone) != 4:
        return False
    x1, y1, x2, y2 = bbox
    zx1, zy1, zx2, zy2 = zone
    # Calculate center of the bounding box
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    # Check if center is within the zone
    return zx1 <= cx <= zx2 and zy1 <= cy <= zy2

class EntryExitLogic:
    def __init__(self, camera_config):
        self.entry_zone = camera_config.get('entry_zone')
        self.exit_zone = camera_config.get('exit_zone')
        # Track vehicle states (simplistic: just remembers if it was last seen in entry/exit)
        # A more robust system would use tracking IDs and state machines
        self.vehicle_states = {} # { vehicle_id (e.g., plate): last_zone }

    def determine_event(self, vehicle_id, bbox):
        """
        Determines if an entry or exit event occurred based on zone crossing.

        Args:
            vehicle_id: A unique identifier for the vehicle (e.g., license plate or tracker ID).
            bbox: The bounding box [x1, y1, x2, y2] of the vehicle.

        Returns:
            'ENTRY', 'EXIT', or None
        """
        event = None
        last_zone = self.vehicle_states.get(vehicle_id)

        in_entry = check_zone_crossing(bbox, self.entry_zone)
        in_exit = check_zone_crossing(bbox, self.exit_zone)

        current_zone = None
        if in_entry:
            current_zone = 'entry'
        elif in_exit:
            current_zone = 'exit'

        if current_zone:
            if current_zone == 'entry' and last_zone != 'entry':
                event = 'ENTRY'
                logging.info(f"Vehicle {vehicle_id} detected entering.")
            elif current_zone == 'exit' and last_zone != 'exit':
                event = 'EXIT'
                logging.info(f"Vehicle {vehicle_id} detected exiting.")

            self.vehicle_states[vehicle_id] = current_zone
        else:
            # Vehicle is not in entry or exit zone, potentially clear state
            # or implement more complex logic (e.g., timeout)
             if vehicle_id in self.vehicle_states:
                 # Simple approach: remove state if not seen in a zone
                 # Better: use tracking and time-based logic
                 # del self.vehicle_states[vehicle_id]
                 pass # Keep state for now in this simple version


        return event

    def draw_zones(self, frame):
        """Draws entry/exit zones on the frame for visualization."""
        if self.entry_zone:
            zx1, zy1, zx2, zy2 = self.entry_zone
            cv2.rectangle(frame, (zx1, zy1), (zx2, zy2), (0, 255, 0), 2) # Green for entry
            cv2.putText(frame, "Entry Zone", (zx1, zy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if self.exit_zone:
            zx1, zy1, zx2, zy2 = self.exit_zone
            cv2.rectangle(frame, (zx1, zy1), (zx2, zy2), (0, 0, 255), 2) # Red for exit
            cv2.putText(frame, "Exit Zone", (zx1, zy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)