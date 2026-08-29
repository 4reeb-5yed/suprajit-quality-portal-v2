import logging
import os
import time
from datetime import date, datetime, timedelta


def ensure_file_safe(filepath: str) -> bool:
    """
    V1 Security Port: Bulletproof check for race conditions, file locks, and active network copies.
    """
    try:
        # 1. Windows File Lock Check
        with open(filepath, "rb") as f:
            f.read(1)

        # 2. Ghost File Check
        size1 = os.path.getsize(filepath)
        if size1 == 0:
            return False

        # 3. Active Network Copy / Race Condition Check
        # Only penalize performance with a sleep if the file was modified in the last 60 seconds
        if time.time() - os.path.getmtime(filepath) < 60:
            time.sleep(0.5)
            if size1 != os.path.getsize(filepath):
                return False

        return True
    except (OSError, PermissionError, FileNotFoundError):
        # File is currently locked by another process (e.g. Excel or network driver)
        return False


from app.database import get_connection
from app.helpers import hash_file
from app.parser import parse_filename

logger = logging.getLogger(__name__)


class SyncEngine:
    def __init__(self, db_path: str, default_storage_base: str):
        self.db_path = db_path

    def _get_folder_customer_mapping(self) -> dict[str, str | None]:
        """
        Retrieves the map of folder_path -> customer_id from folder_mappings.
        Also handles backward compatibility if root_search_path exists in system_settings.
        """
        mapping: dict[str, str | None] = {}
        try:
            conn = get_connection(self.db_path)
            rows = conn.execute("SELECT folder_path, customer_id FROM folder_mappings").fetchall()
            for r in rows:
                if r["folder_path"]:
                    mapping[os.path.normpath(r["folder_path"])] = r["customer_id"]

            # Also check legacy root_search_path if folder_mappings is empty
            if not mapping:
                setting_row = conn.execute("SELECT value FROM system_settings WHERE key = 'root_search_path'").fetchone()
                if setting_row and setting_row["value"]:
                    for p in setting_row["value"].split(";"):
                        p_str = p.strip()
                        if p_str:
                            mapping[os.path.normpath(p_str)] = None
            conn.close()
        except Exception as e:
            logger.error(f"Error reading folder_mappings from DB: {e}")
        return mapping

    def _get_search_roots(self) -> list[str]:
        mapping = self._get_folder_customer_mapping()
        return list(mapping.keys())

    def _resolve_customer_for_path(self, filepath: str, folder_mapping: dict[str, str | None]) -> str | None:
        """Finds the customer_id associated with the root folder containing filepath."""
        norm_file = os.path.normpath(filepath).lower()
        for root_folder, cust_id in folder_mapping.items():
            norm_root = os.path.normpath(root_folder).lower()
            if norm_file.startswith(norm_root):
                return cust_id
        return None

    def _get_custom_pattern(self) -> str:
        try:
            conn = get_connection(self.db_path)
            row = conn.execute("SELECT value FROM system_settings WHERE key = 'filename_regex_pattern'").fetchone()
            conn.close()
            if row and row["value"]:
                return row["value"].strip()
        except Exception as e:
            logger.error(f"Error reading filename_regex_pattern from DB: {e}")
        return ""

    def scan_folder(self, folder_path: str, target_date: date | None) -> list[str]:
        matched_files: list[str] = []
        if not os.path.exists(folder_path):
            logger.warning(f"Source folder not found: {folder_path}")
            return matched_files

        for root, _, files in os.walk(folder_path):
            for filename in files:
                if not filename.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv")):
                    continue

                filepath = os.path.join(root, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    file_date = datetime.fromtimestamp(mtime).date()
                    if target_date is None or file_date == target_date:
                        matched_files.append(filepath)
                except OSError as e:
                    logger.error(f"Error reading file stat for {filepath}: {e}")

        return matched_files

    def run_batch(self, target_date: date | None = None, full_sync: bool = False) -> int:
        if not full_sync and target_date is None:
            target_date = date.today() - timedelta(days=1)
        elif full_sync:
            target_date = None

        folder_mapping = self._get_folder_customer_mapping()
        if not folder_mapping:
            logger.warning("No valid root search path or folder mappings configured. Skipping ingestion.")
            return 0

        total_inserted = 0

        for root_path in folder_mapping.keys():
            inserted = self.process_folder(root_path, target_date)
            total_inserted += inserted

        return total_inserted

    def process_folder(self, source_path: str, target_date: date | None = None) -> int:
        conn = get_connection(self.db_path)

        cursor = conn.cursor()
        t_val = target_date.isoformat() if target_date else "ALL_HISTORICAL"
        cursor.execute("INSERT INTO batch_runs (target_date) VALUES (?)", (t_val,))
        batch_id = cursor.lastrowid
        conn.commit()

        files_to_process = self.scan_folder(source_path, target_date)

        scanned = len(files_to_process)
        inserted = 0
        skipped = 0
        failed = 0
        error_logs = []

        if not files_to_process:
            self._complete_batch(conn, batch_id, scanned, inserted, skipped, failed, "No files found", "completed")
            conn.close()
            return 0

        insert_values = []
        existing_hashes = {row[0] for row in conn.execute("SELECT file_hash FROM reports").fetchall()}
        folder_mapping = self._get_folder_customer_mapping()

        custom_pattern = self._get_custom_pattern()
        for filepath in files_to_process:
            try:
                filename_only = os.path.basename(filepath)
                logger.info(f"Scanning file: {filename_only}")

                if not ensure_file_safe(filepath):
                    skipped += 1
                    logger.warning(f"File locked or actively copying, skipping for next batch: {filename_only}")
                    continue

                parsed = parse_filename(filepath, custom_pattern=custom_pattern)
                if not parsed:
                    failed += 1
                    error_logs.append(f"Unparseable filename: {filepath}")
                    logger.warning(f"Failed to parse filename metadata for: {filename_only}")
                    continue

                # Bind customer_id at ingestion time from the containing folder mapping
                customer_id = self._resolve_customer_for_path(filepath, folder_mapping)

                logger.info(
                    f"Parsed metadata -> Customer: {customer_id}, Recipe: {parsed['recipe_name']}, Date: {parsed['report_date']}, Time: {parsed['report_time']}, Serial: {parsed['serial_raw']}"
                )

                file_hash = hash_file(filepath)
                if file_hash in existing_hashes:
                    skipped += 1
                    continue

                file_size = os.path.getsize(filepath)

                insert_values.append(
                    (
                        batch_id,
                        customer_id,
                        parsed["recipe_name"],
                        parsed["report_date"],
                        parsed["report_time"],
                        parsed["serial_raw"],
                        parsed["serial_normalized"],
                        parsed["original_filename"],
                        filepath,
                        file_hash,
                        file_size,
                    )
                )
                inserted += 1
                logger.info(f"Successfully mapped {filename_only} to Recipe '{parsed['recipe_name']}' (Customer: {customer_id})")

            except Exception as e:
                failed += 1
                error_logs.append(f"Error processing {filepath}: {e!s}")
                logger.error(f"Failed file {filepath}: {e}")

        if insert_values:
            try:
                with conn:
                    conn.executemany(
                        """
                        INSERT OR IGNORE INTO reports 
                        (batch_run_id, customer_id, recipe_name, report_date, report_time, serial_raw, 
                         serial_normalized, original_filename, file_path, file_hash, file_size_bytes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        insert_values,
                    )
            except Exception as e:
                logger.critical(f"Bulk insert failed for batch {batch_id}: {e}")
                self._complete_batch(conn, batch_id, scanned, 0, skipped, failed, f"DB Error: {e!s}", "failed")
                conn.close()
                return 0

        status = "completed"
        self._complete_batch(conn, batch_id, scanned, inserted, skipped, failed, "\n".join(error_logs), status)

        conn.close()
        return inserted

    def _complete_batch(self, conn, batch_id, scanned, inserted, skipped, failed, error_log, status):
        conn.execute(
            """
            UPDATE batch_runs 
            SET run_completed = datetime('now'),
                files_scanned = ?, files_inserted = ?, files_skipped = ?, files_failed = ?,
                error_log = ?, status = ?
            WHERE id = ?
        """,
            (scanned, inserted, skipped, failed, error_log, status, batch_id),
        )
        conn.commit()

    def execute_dry_run(self, target_date: date | None = None) -> str:
        roots = self._get_search_roots()
        if not roots or roots == [""] or roots == ["C:\\"]:
            return "No valid root search path configured. Please configure in Settings."

        trace = []
        trace.append(f"Starting DRY RUN across roots: {roots}")
        trace.append(f"Target Date: {target_date if target_date else 'ALL HISTORICAL'}\n")

        conn = get_connection(self.db_path)
        existing_hashes = {row[0] for row in conn.execute("SELECT file_hash FROM reports").fetchall()}
        conn.close()

        total_scanned = 0
        total_insert = 0
        total_skip = 0
        total_fail = 0

        custom_pattern = self._get_custom_pattern()
        for root_path in roots:
            trace.append(f"-> Scanning: {root_path}")
            files = self.scan_folder(root_path, target_date)
            total_scanned += len(files)

            for fpath in files:
                fname = os.path.basename(fpath)
                parsed = parse_filename(fpath, custom_pattern=custom_pattern)
                if not parsed:
                    trace.append(f"   [FAIL] Could not parse metadata: {fname}")
                    total_fail += 1
                    continue

                fhash = hash_file(fpath)
                if fhash in existing_hashes:
                    trace.append(f"   [SKIP] Already exists in DB: {fname}")
                    total_skip += 1
                else:
                    trace.append(f"   [INSERT] Valid new file: {fname} (Recipe: {parsed['recipe_name']})")
                    total_insert += 1

        trace.append("\n--- DRY RUN SUMMARY ---")

        trace.append(
            f"Scanned: {total_scanned} | Would Insert: {total_insert} | Skipped: {total_skip} | Failed Parse: {total_fail}"
        )
        return "\n".join(trace)
