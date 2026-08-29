from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, row):
        self.id = str(row["id"])
        self.username = row["username"]
        self.email = row["email"]
        self.display_name = row["display_name"]
        self.role = row["role"]
        self.customer_id = row["customer_id"]
        self.access_mode = row["access_mode"] if "access_mode" in row.keys() else "ALL"
        self._is_active = bool(row["is_active"])

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_admin(self):
        return self.role in ("admin", "super_admin")

    @property
    def is_super_admin(self):
        return self.role in ("admin", "super_admin")

    @property
    def is_company_admin(self):
        return self.role == "company_admin"
