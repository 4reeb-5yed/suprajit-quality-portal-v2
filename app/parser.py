import os
import re

DEFAULT_FILENAME_PATTERN = r"^(.+)_(\d{2,4}[-\/]\d{2}[-\/]\d{2,4})_(\d{2}\.\d{2}\.\d{2})_([a-zA-Z0-9_-]+?)(?:\s*\(\d+\)|\s*-\s*Copy)*\.(?:xlsx|csv)$"


def template_to_regex(template: str) -> str:
    """
    Converts a human-readable template like '{RECIPE}_{DATE}_{TIME}_{SERIAL}.xlsx'
    into a strict matching regex capturing exactly (1) recipe, (2) date, (3) time, (4) serial.
    If the template is already a raw regex (starts with ^ or contains capturing groups), it is preserved.
    """
    clean = template.strip()
    if not clean or clean.startswith("#"):
        return ""

    # If it's already a raw regex, return as-is
    if clean.startswith("^") or "(?" in clean or ".*" in clean or "\\d" in clean:
        return clean

    # Escape all regex special characters except braces
    # Placeholders with named groups
    placeholders = {
        "{RECIPE}": r"(?P<recipe>.+?)",
        "{DATE}": r"(?P<date>\d{2,4}[-\/]\d{2}[-\/]\d{2,4})",
        "{TIME}": r"(?P<time>\d{2}\.\d{2}\.\d{2})",
        "{SERIAL}": r"(?P<serial>[a-zA-Z0-9_-]+?)",
    }

    # Verify all 4 required tokens are present in user-friendly template
    upper_clean = clean.upper()
    has_tokens = all(t in upper_clean for t in ("{RECIPE}", "{DATE}", "{TIME}", "{SERIAL}"))

    if not has_tokens:
        # If user typed a custom partial string or raw regex, return it
        return clean

    # Tokenize and escape static literal parts
    import re as _re

    # Replace case-insensitively with standard token placeholders
    pattern = clean
    for token in ("{RECIPE}", "{DATE}", "{TIME}", "{SERIAL}"):
        pattern = _re.sub(_re.escape(token), token, pattern, flags=_re.IGNORECASE)

    # Split by tokens, escape literals, and join
    parts = _re.split(r"({RECIPE}|{DATE}|{TIME}|{SERIAL})", pattern)
    regex_parts = ["^"]
    for part in parts:
        if part == "{RECIPE}":
            regex_parts.append(placeholders["{RECIPE}"])
        elif part == "{DATE}":
            regex_parts.append(placeholders["{DATE}"])
        elif part == "{TIME}":
            regex_parts.append(placeholders["{TIME}"])
        elif part == "{SERIAL}":
            regex_parts.append(placeholders["{SERIAL}"])
        else:
            if part.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv")):
                # Strip extension and make extension matching flexible for excel/csv copy artifacts
                stem = _re.sub(r"\.(xlsx|xls|xlsm|csv)$", "", part, flags=_re.IGNORECASE)
                regex_parts.append(_re.escape(stem))
                regex_parts.append(r"(?:\s*\(\d+\)|\s*-\s*Copy)*\.(?:xlsx|xls|xlsm|csv)")
            else:
                regex_parts.append(_re.escape(part))

    regex_parts.append("$")
    return "".join(regex_parts)


def get_compiled_patterns(custom_pattern: str | None = None) -> list[re.Pattern]:
    """
    Returns a list of compiled regex patterns.
    Supports friendly template tags or raw regex, single patterns or multiple patterns separated by newlines.
    """
    if not custom_pattern or not custom_pattern.strip():
        return [re.compile(DEFAULT_FILENAME_PATTERN, re.IGNORECASE)]

    patterns = []
    for line in custom_pattern.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Convert template if applicable
        regex_str = template_to_regex(line)
        if not regex_str:
            continue
        try:
            patterns.append(re.compile(regex_str, re.IGNORECASE))
        except re.error:
            pass

    if not patterns:
        patterns.append(re.compile(DEFAULT_FILENAME_PATTERN, re.IGNORECASE))

    return patterns


def get_compiled_pattern(custom_pattern: str | None = None) -> re.Pattern:
    """Legacy helper returning the first compiled pattern."""
    return get_compiled_patterns(custom_pattern)[0]


def parse_filename(filename: str, custom_pattern: str | None = None) -> dict[str, str] | None:
    """
    Parses a Suprajit quality report filename and extracts metadata.
    Supports single or multiple regex patterns (separated by newlines).
    Each pattern must capture 4 items: recipe_name, date, time, serial.
    Supports named capture groups (?P<recipe>...), (?P<date>...), (?P<time>...), (?P<serial>...)
    or fallback 4 positional groups (1) recipe_name, (2) date, (3) time, (4) serial.
    """
    # Cleanly extract basename whether filename is an absolute path or relative string with date slashes
    if os.path.isabs(filename):
        basename = os.path.basename(filename)
    elif ("/" in filename or "\\" in filename) and not filename.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv")):
        basename = filename.replace("\\", "/").split("/")[-1]
    elif "\\" in filename:
        # Windows path separators
        basename = filename.split("\\")[-1]
    else:
        basename = filename

    compiled_patterns = get_compiled_patterns(custom_pattern)
    match = None
    for pattern in compiled_patterns:
        m = pattern.match(basename)
        if m:
            groupdict = m.groupdict()
            if all(k in groupdict for k in ("recipe", "date", "time", "serial")) or len(m.groups()) >= 4:
                match = m
                break

    if not match:
        return None

    groupdict = match.groupdict()
    if all(k in groupdict for k in ("recipe", "date", "time", "serial")):
        recipe_name = groupdict["recipe"]
        date_str = groupdict["date"]
        time_str = groupdict["time"]
        serial_raw = groupdict["serial"]
    else:
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
