with open('app/templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add button to the top
content = content.replace('<div class="text-sm text-gray-500">System Health Overview</div>', 
'''<div class="text-sm text-gray-500">System Health Overview</div>
        </div>
        <div>
            <a href="{{ url_for('admin.download_logs') }}" class="btn btn-error btn-sm text-white">
                <i class="fa-solid fa-bug"></i> Download Diagnostic Logs
            </a>''')

# Fix Zombie badge
content = content.replace("{% else %}\n                                <span class=\"badge badge-error text-white\">Failed</span>",
"""{% elif batch.status == 'CRASHED_ZOMBIE' %}
                                <span class="badge badge-error text-white">ZOMBIE (CRASHED)</span>
                            {% else %}
                                <span class="badge badge-error text-white">Failed</span>""")

with open('app/templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
