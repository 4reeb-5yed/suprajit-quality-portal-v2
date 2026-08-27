with open('app/templates/admin/customers.html', 'r') as f:
    c = f.read()

old_input = '<input type="text" name="recipe_name" placeholder="e.g. EV_TPS" required class="input input-bordered w-full" />'
new_input = '''<input list="recipes-list" name="recipe_name" placeholder="Type or select a recipe..." required class="input input-bordered w-full" autocomplete="off" />
                        <datalist id="recipes-list">
                            {% for r in available_recipes %}
                            <option value="{{ r }}">
                            {% endfor %}
                        </datalist>'''

c = c.replace(old_input, new_input)
with open('app/templates/admin/customers.html', 'w') as f:
    f.write(c)
