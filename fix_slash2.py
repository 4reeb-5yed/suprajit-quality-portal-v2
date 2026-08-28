with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "roots == ['C:\']:" in line:
        lines[i] = "        if not roots or roots == [''] or roots == ['C:\\\\']:\n"

with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
