# src/database/db_manager.py

import sqlite3
import datetime
import logging
import yaml # <--- Trying to load config here

# Load configuration
try:
    # This assumes db_manager.py can find 'config/config.yaml' relative to
    # the location where the *main script* (main.py) is run.
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    # If config loading failed (e.g., file not found, YAML error), config might be None
    # OR an exception was caught below.
    DB_PATH = config['database']['path'] # <--- ERROR HAPPENS HERE if config is None
except FileNotFoundError:
    logging.error("Configuration file 'config/config.yaml' not found.")
    # config is not explicitly set to None here, but the error occurs before DB_PATH is assigned
    # if the exception happens. Let's assume config remains unassigned or yaml.safe_load returned None.
    DB_PATH = 'vehicle_log_default.db' # Default fallback
except KeyError:
    logging.error("Database path not specified correctly in config.")
    DB_PATH = 'vehicle_log_default.db' # Default fallback
except Exception as e: # Catching generic exceptions can hide the root cause
    logging.error(f"An unexpected error occurred loading config in db_manager: {e}")
    DB_PATH = 'vehicle_log_default.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        logging.info(f"Database connection established to {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def initialize_database():
    """Creates the necessary tables if they don't exist."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    camera_id TEXT NOT NULL,
                    license_plate TEXT,
                    event_type TEXT NOT NULL CHECK(event_type IN ('ENTRY', 'EXIT', 'DETECTED')),
                    image_path TEXT NULL -- Optional path to saved snapshot
                );
            """)
            conn.commit()
            logging.info("Database initialized successfully.")
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
        finally:
            conn.close()

def log_vehicle_event(camera_id, event_type, license_plate=None, image_path=None):
    """Logs a vehicle event to the database."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now()
            cursor.execute("""
                INSERT INTO vehicle_logs (timestamp, camera_id, license_plate, event_type, image_path)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, camera_id, license_plate, event_type, image_path))
            conn.commit()
            logging.debug(f"Logged event: {timestamp}, {camera_id}, {license_plate}, {event_type}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Error logging event: {e}")
            return None
        finally:
            conn.close()

def get_recent_logs(limit=10):
    """Retrieves the most recent logs."""
    conn = get_db_connection()
    logs = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehicle_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            logs = [dict(row) for row in cursor.fetchall()] # Convert rows to dicts
        except sqlite3.Error as e:
            logging.error(f"Error fetching logs: {e}")
        finally:
            conn.close()
    return logs

# Ensure database is initialized when module is loaded (or call explicitly in main)
# initialize_database() # Consider calling this from main.py instead