# -*- coding: utf-8 -*-
import io
with io.open('app/templates/admin/customers.html', 'r', encoding='utf-8') as f:
    c = f.read()

target_btn = '''        <button class="btn btn-primary suprajit-blue-bg border-none text-white shadow" onclick="addCustomerModal.showModal()">
            <i class="fa-solid fa-plus mr-1"></i> Add New Customer
        </button>'''

new_btns = '''        <div class="flex gap-2">
            <button class="btn bg-gray-800 hover:bg-gray-700 border-none text-white shadow" onclick="addAdminModal.showModal()">
                <i class="fa-solid fa-user-shield mr-1"></i> Add Administrator
            </button>
            <button class="btn btn-primary suprajit-blue-bg border-none text-white shadow" onclick="addCustomerModal.showModal()">
                <i class="fa-solid fa-plus mr-1"></i> Add New Customer
            </button>
        </div>'''

c = c.replace(target_btn, new_btns)

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

c = c.replace('<!-- Add Customer Modal -->', admin_modal + '\n<!-- Add Customer Modal -->')

with io.open('app/templates/admin/customers.html', 'w', encoding='utf-8') as f:
    f.write(c)
