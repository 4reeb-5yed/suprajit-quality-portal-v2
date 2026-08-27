with open('app/mail.py', 'r', encoding='utf-8') as f:
    c = f.read()

if r'\ndef send_heartbeat' in c:
    c = c.replace(r'\ndef send_heartbeat', '\ndef send_heartbeat')

if c.endswith(r'\n'):
    c = c[:-2] + '\n'

with open('app/mail.py', 'w', encoding='utf-8') as f:
    f.write(c)
