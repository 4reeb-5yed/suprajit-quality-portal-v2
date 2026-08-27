import re
import os
from typing import Dict, Optional

# Expected format: {RECIPE}_{DD-MM-YYYY}_{HH.MM.SS}_{SERIAL}.xlsx
# Example: EV_TPS_13-06-2026_22.33.21_12.xlsx
FILENAME_PATTERN = re.compile(
    r"^(.+)_(\d{2}-\d{2}-\d{4})_(\d{2}\.\d{2}\.\d{2})_(\d+)\.xlsx$", 
    re.IGNORECASE
)

def parse_filename(filename: str) -> Optional[Dict[str, str]]:
    """
    Parses a Suprajit quality report filename and extracts metadata.
    Returns None if the filename does not match the expected pattern.
    """
    basename = os.path.basename(filename)
    match = FILENAME_PATTERN.match(basename)
    
    if not match:
        return None
        
    recipe_name = match.group(1)
    date_str = match.group(2)
    time_str = match.group(3)
    serial_raw = match.group(4)
    
    # Normalize date to YYYY-MM-DD for standard SQLite sorting/querying
    day, month, year = date_str.split('-')
    normalized_date = f"{year}-{month}-{day}"
    
    # Normalize time to HH:MM:SS
    normalized_time = time_str.replace('.', ':')
    
    # Normalize serial to zero-padded 4 digits (e.g., "12" -> "0012")
    serial_normalized = serial_raw.zfill(4)
    
    return {
        "recipe_name": recipe_name,
        "report_date": normalized_date,
        "report_time": normalized_time,
        "serial_raw": serial_raw,
        "serial_normalized": serial_normalized,
        "original_filename": basename
    }
