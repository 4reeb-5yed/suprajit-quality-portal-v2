with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('"\\""', '"""')
with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(text)
