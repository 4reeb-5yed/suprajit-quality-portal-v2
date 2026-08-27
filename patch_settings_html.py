with open('app/templates/admin/settings.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add SMTP configuration card before Manual Actions
old_manual = '<!-- Manual Actions -->'
new_smtp = '''<!-- SMTP Settings -->
    <div class="bg-white border border-gray-200 rounded shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200 bg-gray-50">
            <h2 class="text-lg font-bold text-gray-800"><i class="fa-solid fa-envelope mr-2 text-blue-600"></i>Email Server Configuration</h2>
            <p class="text-sm text-gray-500 mt-1">Configure the email account used to send "Forgot Password" links and new user Welcome emails.</p>
        </div>
        <div class="p-6">
            <form method="POST" action="{{ url_for('admin.settings') }}" class="flex flex-col gap-6 max-w-2xl">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="form-control w-full">
                        <label class="label"><span class="label-text font-bold text-gray-700">SMTP Server</span></label>
                        <input type="text" name="mail_server" value="{{ mail_server }}" placeholder="e.g. smtp.gmail.com" class="input input-bordered w-full" />
                    </div>
                    <div class="form-control w-full">
                        <label class="label"><span class="label-text font-bold text-gray-700">SMTP Port</span></label>
                        <input type="number" name="mail_port" value="{{ mail_port }}" placeholder="e.g. 587" class="input input-bordered w-full" />
                    </div>
                </div>

                <div class="form-control w-full">
                    <label class="label"><span class="label-text font-bold text-gray-700">Email Address (Username)</span></label>
                    <input type="email" name="mail_username" value="{{ mail_username }}" placeholder="e.g. factory@gmail.com" class="input input-bordered w-full" />
                </div>
                
                <div class="form-control w-full">
                    <label class="label"><span class="label-text font-bold text-gray-700">Email Password (App Password)</span></label>
                    <input type="password" name="mail_password" value="{{ mail_password }}" placeholder="*********" class="input input-bordered w-full" />
                    <label class="label"><span class="label-text-alt text-gray-500">If using Gmail, you must generate an "App Password" in your Google Account settings.</span></label>
                </div>
                
                <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full md:w-auto self-start">
                    <i class="fa-solid fa-save mr-1"></i> Save Email Config
                </button>
            </form>
        </div>
    </div>

    <!-- Manual Actions -->'''

c = c.replace(old_manual, new_smtp)
with open('app/templates/admin/settings.html', 'w', encoding='utf-8') as f:
    f.write(c)
