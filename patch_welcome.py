with open('app/mail.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_welcome = '''def send_welcome_email(user_email: str, username: str, raw_password: str):
    """Sends a welcome email with initial login credentials."""
    try:
        login_url = f"{request.host_url.rstrip('/')}/login"
        body = f"Welcome to the Suprajit Quality Portal!\\n\\nAn administrator has created an account for you.\\nYou can log in here: {login_url}\\n\\nYour Username: {username}\\nYour Temporary Password: {raw_password}\\n\\nFor security reasons, please log in and change your password immediately or use the Forgot Password link."
        
        return _send_smtp("Welcome to Suprajit Quality Portal - Your Login Info", [user_email], body)'''

new_welcome = '''def send_welcome_email(user_email: str, username: str, raw_password: str, login_url: str = ""):
    """Sends a welcome email with initial login credentials."""
    try:
        if not login_url:
            try:
                login_url = f"{request.host_url.rstrip('/')}/login"
            except:
                login_url = "http://localhost:5000/login"
                
        body = f"Welcome to the Suprajit Quality Portal!\\n\\nAn administrator has created an account for you.\\nYou can log in here: {login_url}\\n\\nYour Username: {username}\\nYour Temporary Password: {raw_password}\\n\\nFor security reasons, please log in and change your password immediately or use the Forgot Password link."
        
        return _send_smtp("Welcome to Suprajit Quality Portal - Your Login Info", [user_email], body)'''

c = c.replace(old_welcome, new_welcome)
with open('app/mail.py', 'w', encoding='utf-8') as f:
    f.write(c)
