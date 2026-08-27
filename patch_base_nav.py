# -*- coding: utf-8 -*-
import io

with io.open('app/templates/base.html', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''                <!-- Right Side Nav -->
                <div class="flex items-center gap-6">
                    {% if current_user.is_authenticated %}
                        {% if current_user.is_admin %}
                            <a href="{{ url_for('admin.dashboard') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-chart-line"></i> Dashboard</a>
                            <a href="{{ url_for('admin.customers') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-users"></i> Customers</a>
                            <a href="{{ url_for('admin.settings') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-cogs"></i> Config</a>
                            <a href="{{ url_for('admin.diagnostics') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-stethoscope"></i> Health</a>
                            <a href="{{ url_for('admin.repair') }}" class="text-sm font-medium text-blue-100 hover:text-white transition flex items-center gap-1.5"><i class="fa-solid fa-wrench"></i> Repair</a>
                            <div class="h-4 w-px bg-blue-700 mx-1"></div> <!-- separator -->'''

replacement = '''                <!-- Right Side Nav -->
                <div class="flex items-center gap-4">
                    {% if current_user.is_authenticated %}
                        {% if current_user.is_admin %}
                            <a href="{{ url_for('admin.dashboard') }}" class="text-sm transition flex items-center gap-1.5 px-3 py-2 rounded {% if request.endpoint == 'admin.dashboard' %}bg-white text-blue-900 font-bold shadow-sm{% else %}font-medium text-blue-100 hover:text-white hover:bg-blue-800{% endif %}"><i class="fa-solid fa-chart-line"></i> Dashboard</a>
                            <a href="{{ url_for('admin.customers') }}" class="text-sm transition flex items-center gap-1.5 px-3 py-2 rounded {% if request.endpoint == 'admin.customers' %}bg-white text-blue-900 font-bold shadow-sm{% else %}font-medium text-blue-100 hover:text-white hover:bg-blue-800{% endif %}"><i class="fa-solid fa-users"></i> Customers</a>
                            <a href="{{ url_for('admin.settings') }}" class="text-sm transition flex items-center gap-1.5 px-3 py-2 rounded {% if request.endpoint == 'admin.settings' %}bg-white text-blue-900 font-bold shadow-sm{% else %}font-medium text-blue-100 hover:text-white hover:bg-blue-800{% endif %}"><i class="fa-solid fa-cogs"></i> Config</a>
                            <a href="{{ url_for('admin.diagnostics') }}" class="text-sm transition flex items-center gap-1.5 px-3 py-2 rounded {% if request.endpoint == 'admin.diagnostics' %}bg-white text-blue-900 font-bold shadow-sm{% else %}font-medium text-blue-100 hover:text-white hover:bg-blue-800{% endif %}"><i class="fa-solid fa-stethoscope"></i> Health</a>
                            <a href="{{ url_for('admin.repair') }}" class="text-sm transition flex items-center gap-1.5 px-3 py-2 rounded {% if request.endpoint == 'admin.repair' %}bg-white text-blue-900 font-bold shadow-sm{% else %}font-medium text-blue-100 hover:text-white hover:bg-blue-800{% endif %}"><i class="fa-solid fa-wrench"></i> Repair</a>
                            <div class="h-4 w-px bg-blue-700 mx-1"></div> <!-- separator -->'''

c = c.replace(target, replacement)

with io.open('app/templates/base.html', 'w', encoding='utf-8') as f:
    f.write(c)
