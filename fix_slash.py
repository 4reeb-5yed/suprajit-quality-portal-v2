with open('app/sync_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace("roots == ['C:\']:", "roots == ['C:\\\\']:")
with open('app/sync_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
