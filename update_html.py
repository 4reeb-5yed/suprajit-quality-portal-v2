import re
with open('app/templates/admin/customers.html', 'r') as f:
    c = f.read()

# Replace folders UI with recipes UI
old_header = '''                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wider"><i class="fa-solid fa-folder-tree mr-2 text-blue-500"></i>Active Recipes & Folders</h3>
                    <button class="btn btn-sm btn-outline text-blue-700" onclick="document.getElementById('addFolderModal-{{ customer.id }}').showModal()">
                        <i class="fa-solid fa-link mr-1"></i> Add Recipe Mapping
                    </button>
                </div>'''

new_header = '''                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wider"><i class="fa-solid fa-tags mr-2 text-blue-500"></i>Allowed Recipes</h3>
                    <button class="btn btn-sm btn-outline text-blue-700" onclick="document.getElementById('addRecipeModal-{{ customer.id }}').showModal()">
                        <i class="fa-solid fa-key mr-1"></i> Grant Recipe Access
                    </button>
                </div>'''
c = c.replace(old_header, new_header)

old_table = '''                        <thead>
                            <tr class="bg-gray-100 text-gray-600">
                                <th>Absolute Folder Path</th>
                                <th>Recipe Name</th>
                                <th class="text-right">Action</th>
                            </tr>
                        </thead>'''
new_table = '''                        <thead>
                            <tr class="bg-gray-100 text-gray-600">
                                <th>Recipe Name</th>
                                <th class="text-right">Action</th>
                            </tr>
                        </thead>'''
c = c.replace(old_table, new_table)

old_tbody = '''                            {% set folders = customer_folders.get(customer.id, []) %}
                            {% if folders %}
                                {% for folder in folders %}
                                <tr>
                                    <td class="font-mono text-sm {% if not folder.is_active %}text-gray-400 line-through{% else %}text-blue-900{% endif %}">
                                        {{ folder.folder_path }}
                                    </td>
                                    <td class="font-mono font-bold {% if not folder.is_active %}text-gray-400{% else %}text-gray-700{% endif %}">
                                        {{ folder.recipe_name }}
                                        {% if not folder.is_active %}<span class="badge badge-sm badge-warning ml-2 text-white">Paused</span>{% endif %}
                                    </td>
                                    <td class="text-right">
                                        <div class="flex justify-end gap-2">
                                            <form method="POST" action="{{ url_for('admin.toggle_folder') }}">
                                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                                <input type="hidden" name="folder_id" value="{{ folder.id }}"/>
                                                {% if folder.is_active %}
                                                    <input type="hidden" name="is_active" value="0"/>
                                                    <button type="submit" class="btn btn-xs btn-outline text-warning" title="Pause Ingestion">
                                                        <i class="fa-solid fa-pause"></i> Pause
                                                    </button>
                                                {% else %}
                                                    <input type="hidden" name="is_active" value="1"/>
                                                    <button type="submit" class="btn btn-xs btn-outline text-success" title="Resume Ingestion">
                                                        <i class="fa-solid fa-play"></i> Resume
                                                    </button>
                                                {% endif %}
                                            </form>
                                            <button class="btn btn-xs btn-ghost text-blue-700" title="Edit Mapping" onclick="document.getElementById('editFolderModal-{{ folder.id }}').showModal()">
                                                <i class="fa-solid fa-edit"></i> Edit
                                            </button>
                                            <form method="POST" action="{{ url_for('admin.delete_folder') }}" onsubmit="return confirm('Are you sure you want to remove this recipe mapping?');">
                                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                                <input type="hidden" name="folder_id" value="{{ folder.id }}"/>
                                                <button type="submit" class="btn btn-xs btn-error text-white" title="Remove"><i class="fa-solid fa-unlink"></i></button>
                                            </form>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Edit Folder Modal -->
                                <dialog id="editFolderModal-{{ folder.id }}" class="modal">
                                    <div class="modal-box bg-white text-left">
                                        <form method="dialog"><button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">?</button></form>
                                        <h3 class="font-bold text-lg text-blue-900 border-b pb-2 mb-4">Edit Recipe Mapping</h3>
                                        <form method="POST" action="{{ url_for('admin.edit_folder') }}" class="space-y-4">
                                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                            <input type="hidden" name="folder_id" value="{{ folder.id }}"/>
                                            <div class="form-control">
                                                <label class="label"><span class="label-text">Absolute Path to Network Folder</span></label>
                                                <input type="text" name="folder_path" value="{{ folder.folder_path }}" class="input input-bordered w-full font-mono text-sm" required>
                                            </div>
                                            <div class="form-control">
                                                <label class="label"><span class="label-text">Recipe Prefix (e.g. EV_TPS)</span></label>
                                                <input type="text" name="recipe_name" value="{{ folder.recipe_name }}" class="input input-bordered w-full font-mono font-bold" required>
                                            </div>
                                            <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full">Save Changes</button>
                                        </form>
                                    </div>
                                    <form method="dialog" class="modal-backdrop"><button>close</button></form>
                                </dialog>
                                {% endfor %}
                            {% else %}
                            <tr>
                                <td colspan="3" class="text-center text-gray-500 py-4 italic">No recipes mapped yet. The engine will skip this customer.</td>
                            </tr>
                            {% endif %}'''

new_tbody = '''                            {% set recipes = customer_recipes.get(customer.id, []) %}
                            {% if recipes %}
                                {% for r in recipes %}
                                <tr>
                                    <td class="font-mono font-bold text-gray-700">
                                        {{ r.recipe_name }}
                                    </td>
                                    <td class="text-right">
                                        <div class="flex justify-end gap-2">
                                            <form method="POST" action="{{ url_for('admin.delete_recipe') }}" onsubmit="return confirm('Remove access to this recipe?');">
                                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                                <input type="hidden" name="customer_id" value="{{ customer.id }}"/>
                                                <input type="hidden" name="recipe_name" value="{{ r.recipe_name }}"/>
                                                <button type="submit" class="btn btn-xs btn-error text-white" title="Remove Access"><i class="fa-solid fa-unlink"></i> Revoke</button>
                                            </form>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            {% else %}
                            <tr>
                                <td colspan="2" class="text-center text-gray-500 py-4 italic">No recipes granted yet. This customer's portal will be empty.</td>
                            </tr>
                            {% endif %}'''
c = c.replace(old_tbody, new_tbody)

# Modal replacement
old_modal = '''        <!-- Add Folder Modal specific to this customer -->
        <dialog id="addFolderModal-{{ customer.id }}" class="modal">
            <div class="modal-box bg-white">
                <form method="dialog"><button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">?</button></form>
                <h3 class="font-bold text-lg text-blue-900 border-b pb-2 mb-4">Map Folder for {{ customer.company_name }}</h3>
                <form method="POST" action="{{ url_for('admin.add_folder') }}" class="space-y-4">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <input type="hidden" name="customer_id" value="{{ customer.id }}">
                    
                    <div class="form-control">
                        <label class="label"><span class="label-text font-bold">Absolute Folder Path</span></label>
                        <input type="text" name="folder_path" placeholder="e.g. C:\Data\TVS or \\server\share\TVS" required class="input input-bordered w-full font-mono text-sm" />
                    </div>

                    <div class="form-control">
                        <label class="label"><span class="label-text font-bold">Recipe Prefix</span></label>
                        <input type="text" name="recipe_name" placeholder="e.g. EV_TPS" required class="input input-bordered w-full" />
                    </div>

                    <div class="modal-action mt-6">
                        <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full">Save Mapping</button>
                    </div>
                </form>
            </div>
            <form method="dialog" class="modal-backdrop"><button>close</button></form>
        </dialog>'''

new_modal = '''        <!-- Add Recipe Modal specific to this customer -->
        <dialog id="addRecipeModal-{{ customer.id }}" class="modal">
            <div class="modal-box bg-white">
                <form method="dialog"><button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">?</button></form>
                <h3 class="font-bold text-lg text-blue-900 border-b pb-2 mb-4">Grant Recipe Access to {{ customer.company_name }}</h3>
                <form method="POST" action="{{ url_for('admin.add_recipe') }}" class="space-y-4">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <input type="hidden" name="customer_id" value="{{ customer.id }}">
                    
                    <div class="form-control">
                        <label class="label"><span class="label-text font-bold">Recipe Prefix</span></label>
                        <input type="text" name="recipe_name" placeholder="e.g. EV_TPS" required class="input input-bordered w-full" />
                    </div>

                    <div class="modal-action mt-6">
                        <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full">Grant Access</button>
                    </div>
                </form>
            </div>
            <form method="dialog" class="modal-backdrop"><button>close</button></form>
        </dialog>'''
c = c.replace(old_modal, new_modal)

with open('app/templates/admin/customers.html', 'w') as f:
    f.write(c)
