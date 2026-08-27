# -*- coding: utf-8 -*-
import io
with io.open('app/templates/admin/customers.html', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''    <!-- Customers List -->
    <div class="grid grid-cols-1 gap-6">'''

replacement = '''    <!-- System Administrators -->
    <div class="bg-gray-800 border border-gray-900 rounded shadow-sm overflow-hidden mb-8">
        <div class="p-5 border-b border-gray-700 bg-gray-900">
            <h2 class="text-xl font-bold text-white"><i class="fa-solid fa-user-shield text-blue-400 mr-2"></i>System Administrators</h2>
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
                                    <button type="submit" class="btn btn-sm btn-error text-white"><i class="fa-solid fa-trash"></i> Delete</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Customers List -->
    <div class="grid grid-cols-1 gap-6">'''

c = c.replace(target, replacement)

# We also need to add delete buttons to the Customer Viewers!
viewer_target = '''                                        {% if u.email %}
                                            <span class="text-xs text-gray-500 block">{{ u.email }}</span>
                                        {% endif %}
                                    </div>
                                </div>
                                <div class="flex items-center gap-2">'''

viewer_replacement = '''                                        {% if u.email %}
                                            <span class="text-xs text-gray-500 block">{{ u.email }}</span>
                                        {% endif %}
                                    </div>
                                </div>
                                <div class="flex items-center gap-2">
                                    <form method="POST" action="{{ url_for('admin.delete_user') }}" onsubmit="return confirm('Are you sure you want to delete this user?');">
                                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                        <input type="hidden" name="user_id" value="{{ u.id }}"/>
                                        <button type="submit" class="btn btn-xs btn-error text-white" title="Delete User"><i class="fa-solid fa-trash"></i></button>
                                    </form>'''

c = c.replace(viewer_target, viewer_replacement)

with io.open('app/templates/admin/customers.html', 'w', encoding='utf-8') as f:
    f.write(c)
