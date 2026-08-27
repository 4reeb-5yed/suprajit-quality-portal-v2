# -*- coding: utf-8 -*-
import io

with io.open('app/templates/admin/diagnostics.html', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''        <!-- System Health Card -->
        <div class="bg-white border border-gray-200 rounded shadow-sm p-6">
            <h3 class="font-bold text-lg border-b pb-2 mb-4"><i class="fa-solid fa-heart-pulse text-red-500 mr-2"></i> System Health</h3>
            
            <div class="flex items-center justify-between py-2 border-b">
                <span class="font-semibold text-gray-600">Web Server Status</span>
                <span class="badge badge-success text-white">ONLINE</span>
            </div>
            
            <div class="flex items-center justify-between py-2 border-b">
                <span class="font-semibold text-gray-600">Database Connection</span>
                <span class="badge badge-success text-white">CONNECTED</span>
            </div>
            
            <div class="flex items-center justify-between py-2 border-b">
                <span class="font-semibold text-gray-600">Last Telemetry Ping</span>
                <span class="text-sm text-gray-800 font-mono">{% if last_run %}{{ last_run.end_time or last_run.start_time }}{% else %}Never{% endif %}</span>
            </div>
            
            <div class="mt-6">
                <p class="text-sm text-gray-500 mb-2">Automated Telemetry reports are sent to the Canspirit Developer Email configured in Settings.</p>
            </div>
        </div>'''

replacement = '''        <!-- Database & Engine Health -->
        <div class="bg-white border border-gray-200 rounded shadow-sm p-6">
            <h3 class="font-bold text-lg border-b pb-2 mb-4"><i class="fa-solid fa-database text-purple-600 mr-2"></i> Database & Engine Health</h3>
            
            <div class="flex items-center justify-between py-2 border-b">
                <span class="font-semibold text-gray-600">Database Size (SQLite WAL)</span>
                <span class="text-sm font-bold text-blue-900">{{ db_size_mb }} MB</span>
            </div>
            
            <div class="flex items-center justify-between py-2 border-b">
                <span class="font-semibold text-gray-600">Total Indexed Reports</span>
                <span class="text-sm font-bold text-gray-800">{{ total_reports }}</span>
            </div>
            
            <div class="flex items-center justify-between py-2 border-b">
                <span class="font-semibold text-gray-600">Ingestion Engine Target</span>
                <span class="badge badge-primary text-white">N-1 (Yesterday)</span>
            </div>
            
            <div class="flex items-center justify-between py-2 border-b">
                <span class="font-semibold text-gray-600">Next Scheduled Run Time</span>
                <span class="badge badge-neutral">{{ sync_time_str }} (24h)</span>
            </div>
            
            <div class="mt-4">
                <p class="text-xs text-gray-500">The background scheduler checks this time every 60 seconds.</p>
            </div>
        </div>'''

c = c.replace(target, replacement)

with io.open('app/templates/admin/diagnostics.html', 'w', encoding='utf-8') as f:
    f.write(c)
