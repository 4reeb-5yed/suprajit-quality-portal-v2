with open('app/templates/admin/customers.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_td = '''                                    <td class="text-right">
                                        <form method="POST" action="{{ url_for('admin.toggle_user') }}">
                                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                            <input type="hidden" name="user_id" value="{{ u.id }}"/>
                                            {% if u.is_active %}
                                                <input type="hidden" name="is_active" value="0"/>
                                                <button type="submit" class="btn btn-xs btn-error text-white"><i class="fa-solid fa-ban"></i> Revoke Access</button>
                                            {% else %}
                                                <input type="hidden" name="is_active" value="1"/>
                                                <button type="submit" class="btn btn-xs btn-success text-white"><i class="fa-solid fa-check"></i> Grant Access</button>
                                            {% endif %}
                                        </form>
                                    </td>'''

new_td = '''                                    <td class="text-right">
                                        <div class="flex justify-end gap-2">
                                            <form method="POST" action="{{ url_for('admin.toggle_user') }}">
                                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                                <input type="hidden" name="user_id" value="{{ u.id }}"/>
                                                {% if u.is_active %}
                                                    <input type="hidden" name="is_active" value="0"/>
                                                    <button type="submit" class="btn btn-xs btn-error btn-outline"><i class="fa-solid fa-ban"></i> Suspend</button>
                                                {% else %}
                                                    <input type="hidden" name="is_active" value="1"/>
                                                    <button type="submit" class="btn btn-xs btn-success text-white"><i class="fa-solid fa-check"></i> Restore</button>
                                                {% endif %}
                                            </form>
                                            
                                            <form method="POST" action="{{ url_for('admin.delete_user') }}" onsubmit="return confirm('Are you sure you want to permanently delete this user account?');">
                                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                                <input type="hidden" name="user_id" value="{{ u.id }}"/>
                                                <button type="submit" class="btn btn-xs btn-error text-white" title="Delete User">
                                                    <i class="fa-solid fa-trash"></i>
                                                </button>
                                            </form>
                                        </div>
                                    </td>'''

c = c.replace(old_td, new_td)
with open('app/templates/admin/customers.html', 'w', encoding='utf-8') as f:
    f.write(c)
