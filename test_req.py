import urllib.request
with open('out.html', 'w', encoding='utf-8') as f:
    f.write(urllib.request.urlopen('http://localhost:5000/admin/').read().decode('utf-8'))
