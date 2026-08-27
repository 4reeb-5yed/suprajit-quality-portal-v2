with open('app/mail.py', 'r') as f:
    c = f.read()

new_func = '''
def send_welcome_email(user_email: str, username: str, raw_password: str):
    """Sends a welcome email with initial login credentials."""
    try:
        from flask import request
        login_url = f"{request.host_url.rstrip('/')}/login"
        
        body = f"""Welcome to the Suprajit Quality Portal!

An administrator has created an account for you.
You can log in here: {login_url}

Your Username: {username}
Your Temporary Password: {raw_password}

For security reasons, please log in and change your password immediately or use the Forgot Password link.
"""
        msg = Message(
            subject="Welcome to Suprajit Quality Portal - Your Login Info",
            recipients=[user_email],
            body=body
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email: {e}")
        return False
'''
c = c + new_func

with open('app/mail.py', 'w') as f:
    f.write(c)
