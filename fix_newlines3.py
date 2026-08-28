with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == 'self._complete_batch(conn, batch_id, scanned, inserted, skipped, failed, "':
        new_lines.append('        self._complete_batch(conn, batch_id, scanned, inserted, skipped, failed, "\\n".join(error_logs), status)\n')
    elif line.strip() == '".join(error_logs), status)':
        continue
    elif line.strip() == 'trace.append(f"Target Date: {target_date if target_date else \'ALL HISTORICAL\'}':
        new_lines.append('        trace.append(f"Target Date: {target_date if target_date else \'ALL HISTORICAL\'}\\n")\n')
    elif line.strip() == '")':
        continue
    elif line.strip() == 'trace.append(f"':
        continue
    elif line.strip() == '--- DRY RUN SUMMARY ---")':
        new_lines.append('        trace.append(f"\\n--- DRY RUN SUMMARY ---")\n')
    elif line.strip() == 'return "':
        new_lines.append('        return "\\n".join(trace)\n')
    elif line.strip() == '".join(trace)':
        continue
    else:
        new_lines.append(line)

with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
