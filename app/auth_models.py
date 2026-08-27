from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, row):
        self.id = str(row['id'])
        self.username = row['username']
        self.email = row['email']
        self.display_name = row['display_name']
        self.role = row['role']
        self.customer_id = row['customer_id']
        self._is_active = bool(row['is_active'])
        
    @property
    def is_active(self):
        return self._is_active
        
    @property
    def is_admin(self):
        return self.role == 'admin'
