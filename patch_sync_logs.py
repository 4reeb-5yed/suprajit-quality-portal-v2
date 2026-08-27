# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''        for filepath in files_to_process:
            try:
                parsed = parse_filename(filepath)
                if not parsed:
                    failed += 1
                    error_logs.append(f"Unparseable filename: {filepath}")
                    continue
                
                file_hash = hash_file(filepath)'''

replacement = '''        for filepath in files_to_process:
            try:
                filename_only = os.path.basename(filepath)
                self.logger.info(f"Scanning file: {filename_only}")
                
                parsed = parse_filename(filepath)
                if not parsed:
                    failed += 1
                    error_logs.append(f"Unparseable filename: {filepath}")
                    self.logger.warning(f"Failed to parse filename metadata for: {filename_only}")
                    continue
                
                self.logger.info(f"Parsed metadata -> Recipe: {parsed['recipe_name']}, Serial: {parsed['serial_raw']}")
                
                file_hash = hash_file(filepath)'''

target2 = '''                insert_values.append((
                    batch_id, parsed['recipe_name'], parsed['report_date'],
                    parsed['report_time'], parsed['serial_raw'], parsed['serial_normalized'],
                    parsed['original_filename'], filepath, file_hash, file_size
                ))
                inserted += 1'''

replacement2 = '''                insert_values.append((
                    batch_id, parsed['recipe_name'], parsed['report_date'],
                    parsed['report_time'], parsed['serial_raw'], parsed['serial_normalized'],
                    parsed['original_filename'], filepath, file_hash, file_size
                ))
                inserted += 1
                self.logger.info(f"Successfully mapped {filename_only} to Recipe '{parsed['recipe_name']}'")'''

c = c.replace(target, replacement)
c = c.replace(target2, replacement2)

with io.open(r'C:\Users\humza\suprajit_v2\app\sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(c)
