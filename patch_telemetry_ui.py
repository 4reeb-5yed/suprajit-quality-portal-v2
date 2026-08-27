# -*- coding: utf-8 -*-
import io
with io.open('app/templates/admin/settings.html', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''                <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full md:w-auto self-start">
                    <i class="fa-solid fa-save mr-1"></i> Save Email Config
                </button>'''

replacement = '''
                <!-- Telemetry Fields -->
                <div class="form-control w-full">
                    <label class="label"><span class="label-text font-bold text-gray-700">Developer Email (Telemetry)</span></label>
                    <input type="text" name="developer_email" value="{{ developer_email }}" class="input input-bordered w-full" placeholder="e.g. admin@canspirit.com" />
                    <label class="label"><span class="label-text-alt text-gray-500">System health and diagnostics will be sent here.</span></label>
                </div>
                
                <div class="form-control w-full">
                    <label class="label"><span class="label-text font-bold text-gray-700">Telemetry Frequency</span></label>
                    <select name="telemetry_frequency" class="select select-bordered w-full">
                        <option value="daily" {% if telemetry_frequency == 'daily' %}selected{% endif %}>Daily Heartbeat</option>
                        <option value="weekly" {% if telemetry_frequency == 'weekly' %}selected{% endif %}>Weekly Heartbeat</option>
                        <option value="monthly" {% if telemetry_frequency == 'monthly' %}selected{% endif %}>Monthly Heartbeat</option>
                        <option value="errors_only" {% if telemetry_frequency == 'errors_only' %}selected{% endif %}>Critical Errors Only</option>
                    </select>
                </div>
                
                <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full md:w-auto self-start mt-4">
                    <i class="fa-solid fa-save mr-1"></i> Save Email & Telemetry Config
                </button>'''

c = c.replace(target, replacement)
c = c.replace('Email Server Configuration', 'Email Server & Telemetry Configuration')

with io.open('app/templates/admin/settings.html', 'w', encoding='utf-8') as f:
    f.write(c)
