with open('app/__init__.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_app = '''def create_app():
    app = Flask(__name__)'''

new_app = '''def create_app():
    import sys
    if getattr(sys, 'frozen', False):
        # If running as PyInstaller EXE
        template_folder = os.path.join(sys._MEIPASS, 'app', 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'app', 'static')
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        app = Flask(__name__)'''

if old_app in c:
    c = c.replace(old_app, new_app)
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(c)
