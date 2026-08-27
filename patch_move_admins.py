# -*- coding: utf-8 -*-
import io
import re

with io.open('app/templates/admin/customers.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Delete System Administrators section from customers.html
pattern = re.compile(r"    <!-- System Administrators -->.*?    <!-- Customers List -->", re.DOTALL)
c = pattern.sub("    <!-- Customers List -->", c)

# Delete Add Administrator buttons
btn_pattern = re.compile(r"        <div class=\"flex gap-2\">\n\s+<button class=\"btn bg-gray-800 hover:bg-gray-700 border-none text-white shadow\" onclick=\"addAdminModal.showModal\(\)\">\n\s+<i class=\"fa-solid fa-user-shield mr-1\"></i> Add Administrator\n\s+</button>\n\s+<button class=\"btn btn-primary suprajit-blue-bg border-none text-white shadow\" onclick=\"addCustomerModal.showModal\(\)\">\n\s+<i class=\"fa-solid fa-plus mr-1\"></i> Add New Customer\n\s+</button>\n\s+</div>", re.DOTALL)
c = btn_pattern.sub('''        <button class="btn btn-primary suprajit-blue-bg border-none text-white shadow" onclick="addCustomerModal.showModal()">
            <i class="fa-solid fa-plus mr-1"></i> Add New Customer
        </button>''', c)

with io.open('app/templates/admin/customers.html', 'w', encoding='utf-8') as f:
    f.write(c)
