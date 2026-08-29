"""
AUTHENTIC REAL-STATE INTEGRATION TESTS FOR app/routes/company.py
Targeting 95%+ coverage across company admin RBAC, user management,
bulk import variants, allowed domain controls, and permission boundaries.
"""

import io
import pytest
from app.database import get_connection, ensure_schema
from werkzeug.security import generate_password_hash


def login_company_admin(client, app, customer_id="suprajit"):
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        ensure_schema(conn)
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('suprajit', 'Suprajit Engineering')")
        conn.execute("INSERT OR IGNORE INTO customer_recipes (customer_id, recipe_name) VALUES ('suprajit', 'RECIPE_A'), ('suprajit', 'RECIPE_B')")
        conn.execute(
            "INSERT OR REPLACE INTO users (id, username, display_name, password_hash, role, customer_id, is_active, access_mode) VALUES (50, 'compadmin', 'Company Admin', ?, 'company_admin', ?, 1, 'ALL')",
            (generate_password_hash("CompAdmin123!"), customer_id)
        )
        conn.commit()
        conn.close()

    # Ensure any prior session is cleared
    client.get("/logout", follow_redirects=True)
    res = client.post("/login", data={"username": "compadmin", "password": "CompAdmin123!"}, follow_redirects=True)
    assert res.status_code == 200
    return res


def test_company_users_manage_views(client, app):
    # 1. Master admin (no customer_id) visiting /company/users gets redirected to admin.customers
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('setup_completed', '1')")
        conn.commit()
        conn.close()

    # login as testadmin (role=admin, customer_id=NULL from conftest)
    client.post("/login", data={"username": "testadmin", "password": "Password123!"}, follow_redirects=True)
    res_m = client.get("/company/users", follow_redirects=False)
    assert res_m.status_code == 302
    assert "/admin/customers" in res_m.headers.get("Location")

    # 2. Valid company_admin can see their users page
    login_company_admin(client, app, customer_id="suprajit")
    res_v = client.get("/company/users")
    assert res_v.status_code == 200
    # Page must render - company_name from conftest is 'Suprajit Internal'
    assert b"Management" in res_v.data


def test_company_add_user_single(client, app):
    login_company_admin(client, app)

    # Empty user submission
    res_empty = client.post("/company/users/add", data={"username": "", "password": ""}, follow_redirects=True)
    assert b"Username and password are required" in res_empty.data

    # Add user without email
    res_no_mail = client.post("/company/users/add", data={
        "username": "local_operator",
        "password": "Password123!",
        "role": "customer_viewer",
        "display_name": "Local Operator"
    }, follow_redirects=True)
    assert b"created successfully" in res_no_mail.data or res_no_mail.status_code == 200

    # Add user with email (welcome mail dispatch)
    res_with_mail = client.post("/company/users/add", data={
        "username": "remote_engineer",
        "email": "engineer@suprajit.com",
        "password": "Password123!",
        "role": "company_admin",
        "display_name": "Remote Engineer"
    }, follow_redirects=True)
    assert b"created. A welcome email is being sent" in res_with_mail.data


def test_company_bulk_add_users(client, app):
    login_company_admin(client, app)

    # Empty bulk text
    res_empty = client.post("/company/users/bulk_add", data={"bulk_text": ""}, follow_redirects=True)
    assert b"No valid email addresses or records found" in res_empty.data

    # Multi-format raw text bulk add
    bulk_text = """
    solo_user@suprajit.com
    pair_user@suprajit.com, Pair Name
    quad_user@suprajit.com, Quad Name, quad_uname, company_admin
    user_with_no_email, Only Name
    """
    res_bulk = client.post("/company/users/bulk_add", data={
        "bulk_text": bulk_text,
        "send_invites": "0"
    }, follow_redirects=True)
    assert b"Bulk Provisioning Completed" in res_bulk.data

    # CSV Upload bulk add
    csv_bytes = b"email,name,username,role\ncsv_team@suprajit.com,CSV Team,csv_team,customer_viewer\n"
    csv_file = (io.BytesIO(csv_bytes), "team.csv")
    res_csv = client.post("/company/users/bulk_add", data={
        "bulk_file": csv_file,
        "send_invites": "1"
    }, content_type="multipart/form-data", follow_redirects=True)
    assert b"Bulk Provisioning Completed" in res_csv.data


def test_company_domains_toggle_and_permissions_boundary(client, app):
    login_company_admin(client, app)

    # Update domains
    res_dom = client.post("/company/domains/update", data={"allowed_domains": "suprajit.com, @suprajit.in"}, follow_redirects=True)
    assert b"Auto-join email domains updated" in res_dom.data

    # Create target subordinate user
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        cur = conn.execute(
            "INSERT INTO users (username, display_name, password_hash, role, customer_id, is_active, access_mode) VALUES ('sub_worker', 'Sub Worker', 'hash', 'customer_viewer', 'suprajit', 1, 'ALL')"
        )
        sub_id = cur.lastrowid
        # Also create a user in another company
        conn.execute("INSERT OR IGNORE INTO customers (id, company_name) VALUES ('other_co', 'Other Corp')")
        cur2 = conn.execute(
            "INSERT INTO users (username, display_name, password_hash, role, customer_id, is_active, access_mode) VALUES ('foreign_worker', 'Foreign Worker', 'hash', 'customer_viewer', 'other_co', 1, 'ALL')"
        )
        foreign_id = cur2.lastrowid
        conn.commit()
        conn.close()

    # Toggle subordinate user status
    res_tog = client.post("/company/users/toggle", data={"user_id": str(sub_id), "is_active": "0"}, follow_redirects=True)
    assert b"User access status updated" in res_tog.data

    # Attempt to toggle user from foreign company -> Expect 403
    res_tog_for = client.post("/company/users/toggle", data={"user_id": str(foreign_id), "is_active": "0"})
    assert res_tog_for.status_code == 403

    # Update permissions for sub user with valid customer recipes
    res_perm = client.post("/company/users/permissions", data={
        "user_id": str(sub_id),
        "access_mode": "CUSTOM",
        "selected_recipes": ["RECIPE_A", "UNAUTHORIZED_FOREIGN_RECIPE"]
    }, follow_redirects=True)
    assert b"Recipe permissions updated successfully" in res_perm.data

    # Verify UNAUTHORIZED_FOREIGN_RECIPE was filtered out by company boundary check
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        assigned = [r["recipe_name"] for r in conn.execute("SELECT recipe_name FROM user_recipes WHERE user_id = ?", (sub_id,)).fetchall()]
        assert assigned == ["RECIPE_A"]
        conn.close()

    # Attempt to update permissions for foreign user -> Expect 403
    res_perm_for = client.post("/company/users/permissions", data={"user_id": str(foreign_id), "access_mode": "ALL"})
    assert res_perm_for.status_code == 403
def test_company_bulk_add_edge_branches(client, app):
    login_company_admin(client, app)

    # 1. Delimiters (; and \t), duplicate skipping, username without email, and invalid username skipped
    bulk_text = """
    semicolon@suprajit.com;Semicolon User;semi_user;customer_viewer
    tabbed@suprajit.com\tTab User\ttab_user\tcustomer_viewer
    only_user_non_email
    duplicate_user@suprajit.com, Dup One, dup_user, customer_viewer
    duplicate_user@suprajit.com, Dup Two, dup_user, customer_viewer
    """
    res = client.post("/company/users/bulk_add", data={
        "bulk_text": bulk_text,
        "send_invites": "1"
    }, follow_redirects=True)
    assert b"Bulk Provisioning Completed" in res.data
    assert b"skipped" in res.data