with open('app/mail.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('app/mail.py', 'w', encoding='utf-8') as f:
    for line in lines:
        if line.strip() == r'\n':
            continue
        f.write(line)
