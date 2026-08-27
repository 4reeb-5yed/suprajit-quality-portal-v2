with open('app/sync_engine.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def scan_folder' in line:
        for j in range(i, min(i+25, len(lines))):
            print(lines[j].rstrip())
        break
