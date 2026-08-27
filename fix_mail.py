with open('app/mail.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('\\ndef', '\\n\\ndef')
c = c.replace('\\n\\n', '\\n\\n') # Clean up double escaped newlines

# wait, just replacing literal '\n' string
c = c.replace(chr(92) + 'n', '\\n')

with open('app/mail.py', 'w', encoding='utf-8') as f:
    f.write(c)
