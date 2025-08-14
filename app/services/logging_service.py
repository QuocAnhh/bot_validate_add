import logging
import csv
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CSV_FILE = "confirmed_trip_requests.csv"
CSV_HEADER = [
    "request_timestamp",
    "origin_address",
    "origin_lat",
    "origin_lng",
    "destination_address",
    "destination_lat",
    "destination_lng",
    "requested_departure_time",
]

def _ensure_csv_file_exists():
    """Create the CSV with a header if it doesn't exist."""
    path = Path(CSV_FILE)
    if not path.is_file():
        logger.info(f"Creating new CSV log file: {CSV_FILE}")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)

def log_trip_request(
    origin_address: str,
    origin_coords: dict,
    destination_address: str,
    destination_coords: dict,
    departure_time_text: str,
):
    """Appends a confirmed trip request to the CSV file."""
    _ensure_csv_file_exists()
    
    timestamp = datetime.now().isoformat()
    
    row_data = [
        timestamp,
        origin_address,
        origin_coords.get("lat") if origin_coords else "N/A",
        origin_coords.get("lng") if origin_coords else "N/A",
        destination_address,
        destination_coords.get("lat") if destination_coords else "N/A",
        destination_coords.get("lng") if destination_coords else "N/A",
        departure_time_text,
    ]
    
    try:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row_data)
        logger.info(f"Successfully logged trip request to {CSV_FILE}")
    except Exception as e:
        logger.error(f"Failed to write to CSV log file {CSV_FILE}: {e}") 