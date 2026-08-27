with open('app/routes/admin.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def trigger_sync' in line:
        for j in range(i, min(i+20, len(lines))):
            print(lines[j].rstrip())
        break
