with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '", "' in line and 'join(error_logs)' in lines[i+1]:
        lines[i] = lines[i].replace('", "', '"\\n".join(error_logs), status)\n')
        lines[i+1] = ""
    if "ALL HISTORICAL'}" in line and '")' in lines[i+1]:
        lines[i] = lines[i].replace("ALL HISTORICAL'}", "ALL HISTORICAL'}\\n\")\n")
        lines[i+1] = ""
    if 'trace.append(f"' in line and '--- DRY RUN SUMMARY ---")' in lines[i+1]:
        lines[i] = lines[i].replace('trace.append(f"', 'trace.append(f"\\n--- DRY RUN SUMMARY ---")\n')
        lines[i+1] = ""
    if 'return "' in line and '".join(trace)' in lines[i+1]:
        lines[i] = lines[i].replace('return "', 'return "\\n".join(trace)\n')
        lines[i+1] = ""

with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
