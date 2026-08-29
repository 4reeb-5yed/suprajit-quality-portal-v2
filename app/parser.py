import os
import re

DEFAULT_FILENAME_PATTERN = r"^(.+)_(\d{2,4}[-\/]\d{2}[-\/]\d{2,4})_(\d{2}\.\d{2}\.\d{2})_([a-zA-Z0-9_-]+?)(?:\s*\(\d+\)|\s*-\s*Copy)*\.(?:xlsx|csv)$"


def get_compiled_pattern(custom_pattern: str | None = None):
    pattern_str = custom_pattern.strip() if custom_pattern and custom_pattern.strip() else DEFAULT_FILENAME_PATTERN
    try:
        return re.compile(pattern_str, re.IGNORECASE)
    except re.error:
        return re.compile(DEFAULT_FILENAME_PATTERN, re.IGNORECASE)


def parse_filename(filename: str, custom_pattern: str | None = None) -> dict[str, str] | None:
    """
    Parses a Suprajit quality report filename and extracts metadata.
    Supports either the standard pattern or a custom regex pattern configured in System Settings.
    The pattern must capture 4 groups: (1) recipe_name, (2) date, (3) time, (4) serial.
    Returns None if the filename does not match the expected pattern.
    """
    # Cleanly extract basename whether filename is an absolute path or relative string with date slashes
    if os.path.isabs(filename):
        basename = os.path.basename(filename)
    elif "/" in filename or "\\" in filename:
        # If string looks like a standalone filename with in-date slashes (e.g. RECIPE_13/06/2026_...)
        # and has no directory separators, preserve it. Otherwise take the final path component.
        has_recipe_and_date = "_" in filename and "-" in filename
        if has_recipe_and_date and not os.path.dirname(filename):
            basename = filename
        else:
            basename = filename.replace("\\", "/").split("/")[-1]
    else:
        basename = filename

    pattern = get_compiled_pattern(custom_pattern)
    match = pattern.match(basename)

    if not match or len(match.groups()) < 4:
        return None

    recipe_name = match.group(1)
    date_str = match.group(2)
    time_str = match.group(3)
    serial_raw = match.group(4)

    from datetime import datetime

    # Strict Date Validation
    normalized_date = None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            normalized_date = dt.strftime("%Y-%m-%d")
            break
        except ValueError:
            pass

    if not normalized_date:
        return None

    # Strict Time Validation (HH.MM.SS)
    try:
        t_parts = [int(p) for p in time_str.split(".")]
        if len(t_parts) != 3 or not (0 <= t_parts[0] <= 23 and 0 <= t_parts[1] <= 59 and 0 <= t_parts[2] <= 59):
            return None
        normalized_time = f"{t_parts[0]:02d}:{t_parts[1]:02d}:{t_parts[2]:02d}"
    except Exception:
        return None

    # Normalize serial to zero-padded 4 digits (e.g., "12" -> "0012")
    serial_clean = serial_raw.strip()
    serial_normalized = serial_clean.zfill(4) if serial_clean.isdigit() else serial_clean

    return {
        "recipe_name": recipe_name.strip(),
        "report_date": normalized_date,
        "report_time": normalized_time,
        "serial_raw": serial_raw,
        "serial_normalized": serial_normalized,
        "original_filename": basename,
    }
