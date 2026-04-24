import unittest
import os
import sqlite3
from datetime import datetime

# Adjust the import path based on how you run your tests.
# If running from the root directory using `python -m unittest discover`,
# this structure should work.
from src.database import db_manager

# Define a temporary database file for testing
TEST_DB_PATH = 'test_vehicle_log.db'

class TestDbManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up for all tests in this class (run once)."""
        # Ensure no old test DB exists
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        # Override the default DB path for testing
        cls.original_db_path = db_manager.DB_PATH
        db_manager.DB_PATH = TEST_DB_PATH
        print(f"Using test database: {db_manager.DB_PATH}")

    @classmethod
    def tearDownClass(cls):
        """Tear down after all tests in this class (run once)."""
        # Clean up the test database file
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
            print(f"Removed test database: {TEST_DB_PATH}")
        # Restore the original DB path
        db_manager.DB_PATH = cls.original_db_path

    def setUp(self):
        """Set up for each test method."""
        # Ensure the database and table are created before each test
        db_manager.initialize_database()
        # Optional: Clear the table before each test if needed
        conn = db_manager.get_db_connection()
        if conn:
            try:
                conn.execute("DELETE FROM vehicle_logs")
                conn.commit()
            finally:
                conn.close()


    def tearDown(self):
        """Tear down after each test method."""
        # Could add cleanup specific to each test if necessary
        pass

    def test_01_initialize_database(self):
        """Test if the table is created correctly."""
        self.assertTrue(os.path.exists(TEST_DB_PATH))
        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.cursor()
        # Check if the table exists by trying to query its schema
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicle_logs';")
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 'vehicle_logs')
        except sqlite3.Error as e:
            self.fail(f"Database query failed during initialization check: {e}")
        finally:
            conn.close()

    def test_02_log_vehicle_event(self):
        """Test logging a single event."""
        cam_id = "test_cam_01"
        event = "ENTRY"
        plate = "TEST1234"
        log_id = db_manager.log_vehicle_event(cam_id, event, license_plate=plate)

        self.assertIsNotNone(log_id)
        self.assertIsInstance(log_id, int)

        # Verify the logged data directly
        conn = db_manager.get_db_connection()
        log = None
        if conn:
             try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM vehicle_logs WHERE id = ?", (log_id,))
                log = cursor.fetchone() # Fetch as tuple
             finally:
                conn.close()

        self.assertIsNotNone(log)
        # Indexes: 0:id, 1:timestamp, 2:camera_id, 3:license_plate, 4:event_type, 5:image_path
        self.assertEqual(log[0], log_id)
        self.assertEqual(log[2], cam_id)
        self.assertEqual(log[3], plate)
        self.assertEqual(log[4], event)
        # Check timestamp is recent (within a reasonable margin, e.g., 5 seconds)
        log_time = datetime.fromisoformat(log[1])
        time_diff = datetime.now() - log_time
        self.assertTrue(abs(time_diff.total_seconds()) < 5)


    def test_03_get_recent_logs(self):
        """Test retrieving recent logs."""
        # Log a few events
        db_manager.log_vehicle_event("cam01", "ENTRY", "PLATEA")
        # Add a small delay to ensure different timestamps
        import time
        time.sleep(0.01)
        db_manager.log_vehicle_event("cam02", "EXIT", "PLATEB")
        time.sleep(0.01)
        log_id_c = db_manager.log_vehicle_event("cam01", "DETECTED", "PLATEC")

        # Retrieve logs (default limit is 10, should get all 3)
        logs = db_manager.get_recent_logs()
        self.assertEqual(len(logs), 3)

        # Check if the most recent log is the last one we added (PLATEC)
        self.assertEqual(logs[0]['id'], log_id_c)
        self.assertEqual(logs[0]['license_plate'], "PLATEC")
        self.assertEqual(logs[0]['event_type'], "DETECTED")

        # Check the second most recent (PLATEB)
        self.assertEqual(logs[1]['license_plate'], "PLATEB")
        self.assertEqual(logs[1]['event_type'], "EXIT")

        # Check the oldest (PLATEA)
        self.assertEqual(logs[2]['license_plate'], "PLATEA")
        self.assertEqual(logs[2]['event_type'], "ENTRY")

        # Test limit
        logs_limited = db_manager.get_recent_logs(limit=1)
        self.assertEqual(len(logs_limited), 1)
        self.assertEqual(logs_limited[0]['id'], log_id_c)


# Allows running the tests directly from the command line
if __name__ == '__main__':
    unittest.main()