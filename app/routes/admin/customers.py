from flask import flash, g, redirect, render_template, request, url_for

from app.database import (
    DELETE_CUSTOMER,
    DELETE_CUSTOMER_RECIPE,
    DELETE_USER_RECIPES,
    GET_ALL_CUSTOMERS,
    GET_CUSTOMER_BY_ID,
    GET_USERS_BY_CUSTOMER,
    INSERT_CUSTOMER,
    INSERT_CUSTOMER_RECIPE,
    INSERT_USER_RECIPE,
    TOGGLE_CUSTOMER_SUSPENSION,
    UPDATE_CUSTOMER,
    UPDATE_USER_ACCESS_MODE,
)
from app.routes.admin import admin_bp


@admin_bp.route("/customers", methods=["GET"])
def customers():
    customer_list = g.db.execute(GET_ALL_CUSTOMERS).fetchall()

    # Fetch all recipes and group by customer_id
    recipes_raw = g.db.execute("SELECT * FROM customer_recipes").fetchall()
    customer_recipes = {}
    for r in recipes_raw:
        cid = r["customer_id"]
        if cid not in customer_recipes:
            customer_recipes[cid] = []
        customer_recipes[cid].append(r)

    # Fetch all users belonging to client companies
    users_raw = g.db.execute("SELECT * FROM users WHERE customer_id IS NOT NULL ORDER BY id DESC").fetchall()
    customer_users = {}
    for u in users_raw:
        cid = u["customer_id"]
        if cid not in customer_users:
            customer_users[cid] = []
        customer_users[cid].append(u)

    available_recipes = [
        r["recipe_name"]
        for r in g.db.execute("SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name").fetchall()
    ]
    return render_template(
        "admin/customers.html",
        customers=customer_list,
        customer_recipes=customer_recipes,
        customer_users=customer_users,
        available_recipes=available_recipes,
    )


@admin_bp.route("/customers/add", methods=["POST"])
def add_customer():
    c_id = request.form.get("id", "").strip().lower()
    c_name = request.form.get("company_name", "").strip()

    if not c_id or not c_name:
        flash("Customer ID and Name are required.", "error")
    else:
        try:
            g.db.execute(INSERT_CUSTOMER, (c_id, c_name))
            g.db.commit()
            flash(f"Customer '{c_name}' added successfully.", "success")
        except Exception as e:
            flash(f"Database Error: {e}", "error")

    return redirect(url_for("admin.customers"))


@admin_bp.route("/customers/<customer_id>", methods=["GET"])
def customer_detail(customer_id):
    customer = g.db.execute(GET_CUSTOMER_BY_ID, (customer_id,)).fetchone()
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for("admin.customers"))

    users = g.db.execute(GET_USERS_BY_CUSTOMER, (customer_id,)).fetchall()
    allowed_recipes = g.db.execute(
        "SELECT * FROM customer_recipes WHERE customer_id = ? ORDER BY recipe_name", (customer_id,)
    ).fetchall()
    already_granted = {r["recipe_name"] for r in allowed_recipes}

    # Filter available recipes to only those NOT already assigned to this customer
    all_known_recipes = [
        r["recipe_name"]
        for r in g.db.execute("SELECT DISTINCT recipe_name FROM reports ORDER BY recipe_name").fetchall()
    ]
    available_recipes = [r for r in all_known_recipes if r not in already_granted]

    # Fetch granular assignments for each user
    user_assigned_recipes = {}
    user_recipe_counts = {}
    for u in users:
        u_recipes = [
            row["recipe_name"]
            for row in g.db.execute("SELECT recipe_name FROM user_recipes WHERE user_id = ?", (u["id"],)).fetchall()
        ]
        user_assigned_recipes[u["id"]] = u_recipes
        user_recipe_counts[u["id"]] = len(u_recipes)

    return render_template(
        "admin/customer_detail.html",
        customer=customer,
        users=users,
        allowed_recipes=allowed_recipes,
        available_recipes=available_recipes,
        user_assigned_recipes=user_assigned_recipes,
        user_recipe_counts=user_recipe_counts,
    )


@admin_bp.route("/customers/update_user_permissions", methods=["POST"])
def update_user_recipe_permissions():
    user_id = request.form.get("user_id")
    customer_id = request.form.get("customer_id")
    access_mode = request.form.get("access_mode", "ALL")
    selected_recipes = request.form.getlist("selected_recipes")

    if user_id:
        g.db.execute(UPDATE_USER_ACCESS_MODE, (access_mode, user_id))
        g.db.execute(DELETE_USER_RECIPES, (user_id,))
        if access_mode == "CUSTOM":
            for r_name in selected_recipes:
                g.db.execute(INSERT_USER_RECIPE, (user_id, r_name.strip()))
        g.db.commit()
        flash("Recipe access permissions updated successfully.", "success")

    if customer_id:
        return redirect(url_for("admin.customer_detail", customer_id=customer_id))
    return redirect(url_for("admin.customers"))


@admin_bp.route("/customers/update_domains", methods=["POST"])
def update_allowed_domains():
    customer_id = request.form.get("customer_id")
    allowed_domains = request.form.get("allowed_domains", "").strip()
    redirect_url = request.form.get("redirect_url")

    if customer_id:
        # Clean and normalize domains (e.g. mahindra.com, tvs.com)
        domains_list = [
            d.strip().lower().lstrip("@") for d in allowed_domains.replace(";", ",").split(",") if d.strip()
        ]
        cleaned_domains = ", ".join(domains_list) if domains_list else None

        g.db.execute("UPDATE customers SET allowed_domains = ? WHERE id = ?", (cleaned_domains, customer_id))
        g.db.commit()
        flash("Auto-join email domains updated for client.", "success")

    if redirect_url:
        return redirect(redirect_url)
    return redirect(url_for("admin.customers"))


@admin_bp.route("/customers/add_recipe", methods=["POST"])
def add_recipe():
    customer_id = request.form.get("customer_id")
    recipe_name = request.form.get("recipe_name", "").strip()
    redirect_url = request.form.get("redirect_url")

    if not recipe_name:
        flash("Recipe prefix is required.", "error")
    else:
        try:
            g.db.execute(INSERT_CUSTOMER_RECIPE, (customer_id, recipe_name))
            g.db.commit()
            flash("Recipe access granted.", "success")
        except Exception as e:
            flash(f"Database Error: {e}", "error")

    if redirect_url:
        return redirect(redirect_url)
    return redirect(url_for("admin.customers"))


@admin_bp.route("/customers/delete_recipe", methods=["POST"])
def delete_recipe():
    customer_id = request.form.get("customer_id")
    recipe_name = request.form.get("recipe_name")
    redirect_url = request.form.get("redirect_url")
    if customer_id and recipe_name:
        g.db.execute(DELETE_CUSTOMER_RECIPE, (customer_id, recipe_name))
        g.db.commit()
        flash("Recipe access removed successfully.", "success")

    if redirect_url:
        return redirect(redirect_url)
    return redirect(url_for("admin.customers"))


@admin_bp.route("/customers/edit", methods=["POST"])
def edit_customer():
    customer_id = request.form.get("customer_id")
    company_name = request.form.get("company_name", "").strip()

    if company_name:
        g.db.execute(UPDATE_CUSTOMER, (company_name, customer_id))
        g.db.commit()
        flash(f"Customer '{company_name}' updated successfully.", "success")

    return redirect(url_for("admin.customers"))


@admin_bp.route("/customers/suspend", methods=["POST"])
@admin_bp.route("/customers/toggle", methods=["POST"], endpoint="toggle_customer")
def suspend_customer():
    customer_id = request.form.get("customer_id")
    new_state = int(request.form.get("portal_suspended", 1))

    if customer_id:
        g.db.execute(TOGGLE_CUSTOMER_SUSPENSION, (new_state, customer_id))
        g.db.commit()
        if new_state == 1:
            flash(f"Customer '{customer_id}' has been SUSPENDED. None of their users can log in.", "success")
        else:
            flash(f"Customer '{customer_id}' has been RESTORED. Portal access is active.", "success")

    redirect_url = request.form.get("redirect_url")
    if redirect_url:
        return redirect(redirect_url)
    return redirect(url_for("admin.customers"))


@admin_bp.route("/customers/delete", methods=["POST"])
def delete_customer():
    customer_id = request.form.get("customer_id")
    if customer_id:
        try:
            g.db.execute(DELETE_CUSTOMER, (customer_id,))
            g.db.commit()
            flash(f"Customer '{customer_id}' has been permanently deleted.", "success")
        except Exception as e:
            flash(f"Database Error: {e}", "error")

    return redirect(url_for("admin.customers"))
