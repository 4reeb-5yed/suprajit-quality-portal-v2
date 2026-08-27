# -*- coding: utf-8 -*-
import io

with io.open('app/templates/admin/settings.html', 'r', encoding='utf-8') as f:
    c = f.read()

admin_block = '''
    <!-- System Administrators -->
    <div class="bg-gray-800 border border-gray-900 rounded shadow-sm overflow-hidden">
        <div class="p-5 border-b border-gray-700 bg-gray-900 flex justify-between items-center">
            <div>
                <h2 class="text-xl font-bold text-white"><i class="fa-solid fa-user-shield text-blue-400 mr-2"></i>System Administrators</h2>
                <p class="text-sm text-gray-400 mt-1">Manage global IT access.</p>
            </div>
            <button class="btn btn-sm btn-primary border-none text-white shadow" onclick="addAdminModal.showModal()">
                <i class="fa-solid fa-plus mr-1"></i> Add Administrator
            </button>
        </div>
        <div class="p-5">
            <div class="overflow-x-auto">
                <table class="table w-full text-gray-300">
                    <thead>
                        <tr class="text-gray-400 border-gray-700">
                            <th>Username</th>
                            <th>Display Name</th>
                            <th>Email</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for admin in system_admins %}
                        <tr class="border-gray-700 hover:bg-gray-700">
                            <td class="font-bold">{{ admin.username }}</td>
                            <td>{{ admin.display_name }}</td>
                            <td>{{ admin.email or 'N/A' }}</td>
                            <td>
                                <form method="POST" action="{{ url_for('admin.delete_user') }}" onsubmit="return confirm('Are you sure you want to delete this Administrator?');">
                                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                    <input type="hidden" name="user_id" value="{{ admin.id }}"/>
                                    <button type="submit" class="btn btn-xs btn-error text-white"><i class="fa-solid fa-trash"></i> Delete</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
'''

admin_modal = '''
<!-- Add Master Admin Modal -->
<dialog id="addAdminModal" class="modal">
    <div class="modal-box bg-white">
        <form method="dialog"><button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button></form>
        <h3 class="font-bold text-lg text-gray-800 border-b pb-2 mb-4"><i class="fa-solid fa-user-shield text-blue-600 mr-2"></i>Create Master Administrator</h3>
        <form method="POST" action="{{ url_for('admin.add_user') }}" class="space-y-3">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <input type="hidden" name="role" value="admin">
            
            <div class="form-control">
                <label class="label"><span class="label-text font-bold">Username</span></label>
                <input type="text" name="username" placeholder="e.g. john_it" required class="input input-sm input-bordered w-full" />
            </div>
            <div class="form-control">
                <label class="label"><span class="label-text font-bold">Display Name</span></label>
                <input type="text" name="display_name" placeholder="e.g. John Doe" required class="input input-sm input-bordered w-full" />
            </div>
            <div class="form-control">
                <label class="label"><span class="label-text font-bold">Contact Email</span></label>
                <input type="email" name="email" placeholder="Required for password resets" required class="input input-sm input-bordered w-full" />
            </div>
            <div class="form-control">
                <label class="label"><span class="label-text font-bold">Temporary Password</span></label>
                <input type="text" name="password" required class="input input-sm input-bordered w-full" />
            </div>
            <div class="modal-action mt-4">
                <button type="submit" class="btn bg-gray-800 text-white w-full border-none hover:bg-gray-700">Create Administrator</button>
            </div>
        </form>
    </div>
    <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>
'''

c = c.replace('<!-- Batch Ingestion Settings -->', admin_block + '\n    <!-- Batch Ingestion Settings -->')
c = c + '\n' + admin_modal

with io.open('app/templates/admin/settings.html', 'w', encoding='utf-8') as f:
    f.write(c)
