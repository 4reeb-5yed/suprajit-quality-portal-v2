with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, l in enumerate(lines[140:190]):
        print(f"{i+141}: {l.strip()}")
