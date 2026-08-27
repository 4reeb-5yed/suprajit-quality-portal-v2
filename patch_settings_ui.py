# -*- coding: utf-8 -*-
import io
with io.open('app/templates/admin/settings.html', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''<div class="form-control w-full">
                    <label class="label"><span class="label-text font-bold text-gray-700">Mail App Password</span></label>
                    <input type="password" name="mail_password" value="{{ mail_password }}" class="input input-bordered w-full" placeholder="••••••••" />
                </div>'''

replacement = target + '''
                
                <div class="form-control w-full">
                    <label class="label"><span class="label-text font-bold text-gray-700">Canspirit Developer Email</span></label>
                    <input type="text" name="developer_email" value="{{ developer_email }}" class="input input-bordered w-full" placeholder="admin@canspirit.com" />
                </div>
                
                <div class="form-control w-full">
                    <label class="label"><span class="label-text font-bold text-gray-700">Telemetry Frequency</span></label>
                    <select name="telemetry_frequency" class="select select-bordered w-full">
                        <option value="daily" {% if telemetry_frequency == 'daily' %}selected{% endif %}>Daily Heartbeat</option>
                        <option value="weekly" {% if telemetry_frequency == 'weekly' %}selected{% endif %}>Weekly Heartbeat</option>
                        <option value="monthly" {% if telemetry_frequency == 'monthly' %}selected{% endif %}>Monthly Heartbeat</option>
                        <option value="errors_only" {% if telemetry_frequency == 'errors_only' %}selected{% endif %}>Critical Errors Only</option>
                    </select>
                </div>'''

c = c.replace(target, replacement)

# Change header
c = c.replace('SMTP Mail Settings', 'SMTP Mail & Telemetry Settings')

with io.open('app/templates/admin/settings.html', 'w', encoding='utf-8') as f:
    f.write(c)
