with open('app/routes/portal.py', 'r', encoding='utf-8') as f:
    text = f.read()

import_time = "import time\n"
if "import time" not in text:
    text = text.replace("import os", "import os\nimport time")

search_def = "def search_results():"
new_search = "def search_results():\n    start_time = time.time()\n"

text = text.replace(search_def, new_search)

render_str = "return render_template_string(table_html, reports=results)"
new_render = '''
    # Record metrics
    latency_ms = (time.time() - start_time) * 1000
    try:
        g.db.execute("INSERT INTO search_metrics (latency_ms) VALUES (?)", (latency_ms,))
        g.db.commit()
    except:
        pass
    return render_template_string(table_html, reports=results)
'''
text = text.replace(render_str, new_render.strip())

with open('app/routes/portal.py', 'w', encoding='utf-8') as f:
    f.write(text)
