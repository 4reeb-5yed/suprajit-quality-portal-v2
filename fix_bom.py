with open('pyproject.toml', 'rb') as f:
    content = f.read()

# Strip BOM if it exists
if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]
elif content.startswith(b'\xff\xfe'): # UTF-16
    content = content.decode('utf-16').encode('utf-8')

with open('pyproject.toml', 'wb') as f:
    f.write(content)
