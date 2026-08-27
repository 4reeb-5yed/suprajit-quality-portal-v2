with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_thread = '''            def background_mail():
                with app_context:
                    send_welcome_email(email, username, password)
            threading.Thread(target=background_mail).start()'''

new_thread = '''            from flask import request
            host_login = f"{request.host_url.rstrip('/')}/login"
            def background_mail(url):
                with app_context:
                    send_welcome_email(email, username, password, url)
            threading.Thread(target=background_mail, args=(host_login,)).start()'''

c = c.replace(old_thread, new_thread)
with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
