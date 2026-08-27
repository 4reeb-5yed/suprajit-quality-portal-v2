with open('app/templates/admin/customers.html', 'r') as f:
    c = f.read()

start_idx = c.find('<!-- Recipes/Folders Section -->')
end_idx = c.find('<!-- Access Management Section -->')

new_section = '''<!-- Recipes/Folders Section -->
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wider"><i class="fa-solid fa-tags mr-2 text-blue-500"></i>Allowed Recipes</h3>
                    <button class="btn btn-sm btn-outline text-blue-700" onclick="document.getElementById('addRecipeModal-{{ customer.id }}').showModal()">
                        <i class="fa-solid fa-key mr-1"></i> Grant Recipe Access
                    </button>
                </div>
                
                <div class="overflow-x-auto mb-8">
                    <table class="table table-zebra table-sm w-full border border-gray-200">
                        <thead>
                            <tr class="bg-gray-100 text-gray-600">
                                <th>Recipe Name</th>
                                <th class="text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% set recipes = customer_recipes.get(customer.id, []) %}
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
                            {% endif %}
                        </tbody>
                    </table>
                </div>

                '''
c = c[:start_idx] + new_section + c[end_idx:]

# Now replace the Add Folder Modal with Add Recipe Modal
start_idx = c.find('<!-- Add Folder Modal specific to this customer -->')
end_idx = c.find('{% else %}', start_idx)

new_modal = '''<!-- Add Recipe Modal specific to this customer -->
        <dialog id="addRecipeModal-{{ customer.id }}" class="modal">
            <div class="modal-box bg-white">
                <form method="dialog"><button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">?</button></form>
                <h3 class="font-bold text-lg text-blue-900 border-b pb-2 mb-4">Grant Recipe Access to {{ customer.company_name }}</h3>
                <form method="POST" action="{{ url_for('admin.add_recipe') }}" class="space-y-4">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <input type="hidden" name="customer_id" value="{{ customer.id }}">
                    
                    <div class="form-control">
                        <label class="label"><span class="label-text font-bold">Recipe Prefix (e.g. EV_TPS)</span></label>
                        <input type="text" name="recipe_name" placeholder="e.g. EV_TPS" required class="input input-bordered w-full" />
                    </div>

                    <div class="modal-action mt-6">
                        <button type="submit" class="btn btn-primary suprajit-blue-bg border-none text-white w-full">Grant Access</button>
                    </div>
                </form>
            </div>
            <form method="dialog" class="modal-backdrop"><button>close</button></form>
        </dialog>
        
        '''

if start_idx != -1:
    c = c[:start_idx] + new_modal + c[end_idx:]

with open('app/templates/admin/customers.html', 'w') as f:
    f.write(c)
