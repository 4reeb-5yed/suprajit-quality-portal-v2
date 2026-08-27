with open('app/routes/admin.py', 'r') as f:
    c = f.read()

old_add = '''    try:
        g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, 'customer_viewer', customer_id))
        g.db.commit()
        flash(f"Login account '{username}' created successfully.", "success")'''

new_add = '''    try:
        g.db.execute(INSERT_USER, (username, email, pwd_hash, display_name, 'customer_viewer', customer_id))
        g.db.commit()
        
        # Send welcome email if email was provided
        if email:
            from app.mail import send_welcome_email
            # Run in a separate thread so the admin page doesn't hang if SMTP is slow
            import threading
            from flask import current_app
            app_context = current_app._get_current_object().app_context()
            def background_mail():
                with app_context:
                    send_welcome_email(email, username, password)
            threading.Thread(target=background_mail).start()
            flash(f"Login account '{username}' created. A welcome email is being sent to {email}.", "success")
        else:
            flash(f"Login account '{username}' created successfully.", "success")'''

c = c.replace(old_add, new_add)
with open('app/routes/admin.py', 'w') as f:
    f.write(c)
