with open('app/templates/admin/settings.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_html = '''                    <div class="grid grid-cols-1 gap-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text font-bold">Canspirit Developer Email (For Status Reports)</span>
                            </label>
                            <input type="email" name="developer_email" value="{{ developer_email }}" class="input input-bordered w-full" placeholder="e.g. admin@canspirit.com" />
                            <label class="label"><span class="label-text-alt text-gray-500">The software will send automated daily health reports to this email.</span></label>
                        </div>
                    </div>'''

new_html = '''                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text font-bold">Canspirit Developer Email</span>
                            </label>
                            <input type="email" name="developer_email" value="{{ developer_email }}" class="input input-bordered w-full" placeholder="e.g. admin@canspirit.com" />
                            <label class="label"><span class="label-text-alt text-gray-500">Telemetry reports will be sent to this email.</span></label>
                        </div>
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text font-bold">Success Email Frequency</span>
                            </label>
                            <select name="telemetry_frequency" class="select select-bordered w-full">
                                <option value="daily" {% if telemetry_frequency == 'daily' %}selected{% endif %}>Daily (Every Sync)</option>
                                <option value="weekly" {% if telemetry_frequency == 'weekly' %}selected{% endif %}>Weekly (Every Monday)</option>
                                <option value="monthly" {% if telemetry_frequency == 'monthly' %}selected{% endif %}>Monthly (1st of Month)</option>
                                <option value="errors_only" {% if telemetry_frequency == 'errors_only' %}selected{% endif %}>Errors Only (Never send successes)</option>
                            </select>
                            <label class="label"><span class="label-text-alt text-gray-500">Note: Critical Errors will ALWAYS be emailed immediately regardless of this setting.</span></label>
                        </div>
                    </div>'''

c = c.replace(old_html, new_html)

with open('app/templates/admin/settings.html', 'w', encoding='utf-8') as f:
    f.write(c)
