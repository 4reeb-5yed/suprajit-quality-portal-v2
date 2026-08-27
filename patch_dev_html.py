with open('app/templates/admin/settings.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_html = '''                    <div class="form-control mt-6">
                        <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full">Save Configuration</button>
                    </div>'''

new_html = '''                    <h3 class="text-lg font-bold text-gray-800 mt-6 mb-2 border-b pb-2"><i class="fa-solid fa-code text-primary mr-2"></i> Developer Telemetry</h3>
                    <div class="grid grid-cols-1 gap-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text font-bold">Canspirit Developer Email (For Status Reports)</span>
                            </label>
                            <input type="email" name="developer_email" value="{{ developer_email }}" class="input input-bordered w-full" placeholder="e.g. admin@canspirit.com" />
                            <label class="label"><span class="label-text-alt text-gray-500">The software will send automated daily health reports to this email.</span></label>
                        </div>
                    </div>
                    
                    <div class="form-control mt-6">
                        <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full">Save Configuration</button>
                    </div>'''
                    
c = c.replace(old_html, new_html)

with open('app/templates/admin/settings.html', 'w', encoding='utf-8') as f:
    f.write(c)
