import re
import os
from typing import Dict, Optional

DEFAULT_FILENAME_PATTERN = r"^(.+)_(\d{2}-\d{2}-\d{4})_(\d{2}\.\d{2}\.\d{2})_([a-zA-Z0-9_-]+?)(?:\s*\(\d+\)|\s*-\s*Copy)*\.(?:xlsx|csv)$"

def get_compiled_pattern(custom_pattern: Optional[str] = None):
    pattern_str = custom_pattern.strip() if custom_pattern and custom_pattern.strip() else DEFAULT_FILENAME_PATTERN
    try:
        return re.compile(pattern_str, re.IGNORECASE)
    except re.error:
        return re.compile(DEFAULT_FILENAME_PATTERN, re.IGNORECASE)

def parse_filename(filename: str, custom_pattern: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Parses a Suprajit quality report filename and extracts metadata.
    Supports either the standard pattern or a custom regex pattern configured in System Settings.
    The pattern must capture 4 groups: (1) recipe_name, (2) date, (3) time, (4) serial.
    Returns None if the filename does not match the expected pattern.
    """
    basename = os.path.basename(filename)
    pattern = get_compiled_pattern(custom_pattern)
    match = pattern.match(basename)
    
    if not match or len(match.groups()) < 4:
        return None
        
    recipe_name = match.group(1)
    date_str = match.group(2)
    time_str = match.group(3)
    serial_raw = match.group(4)
    
    # Normalize date to YYYY-MM-DD
    if '-' in date_str:
        parts = date_str.split('-')
        if len(parts) == 3:
            if len(parts[0]) == 4: # YYYY-MM-DD
                normalized_date = date_str
            else: # DD-MM-YYYY
                day, month, year = parts
                normalized_date = f"{year}-{month}-{day}"
        else:
            normalized_date = date_str
    elif '/' in date_str:
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            normalized_date = f"{year}-{month}-{day}"
        else:
            normalized_date = date_str
    else:
        normalized_date = date_str
    
    # Normalize time to HH:MM:SS
    normalized_time = time_str.replace('.', ':')
    
    # Normalize serial to zero-padded 4 digits (e.g., "12" -> "0012")
    serial_normalized = serial_raw.zfill(4) if serial_raw.isdigit() else serial_raw
    
    return {
        "recipe_name": recipe_name,
        "report_date": normalized_date,
        "report_time": normalized_time,
        "serial_raw": serial_raw,
        "serial_normalized": serial_normalized,
        "original_filename": basename
    }
