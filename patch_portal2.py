with open('app/routes/portal.py', 'r', encoding='utf-8') as f:
    text = f.read()

orig_return = "return render_template('partials/results_table.html', reports=reports)"
new_return = '''
    latency_ms = (time.time() - start_time) * 1000
    try:
        g.db.execute("INSERT INTO search_metrics (latency_ms) VALUES (?)", (latency_ms,))
        g.db.commit()
    except Exception as e:
        print("Metric error:", e)
    return render_template('partials/results_table.html', reports=reports)
'''
text = text.replace(orig_return, new_return.strip())

with open('app/routes/portal.py', 'w', encoding='utf-8') as f:
    f.write(text)
