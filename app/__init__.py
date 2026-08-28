from flask import Flask, g
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

import os
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(app):
    # Setup Enterprise Log Rotation inside the data directory
    log_dir = os.path.join(os.path.dirname(app.config['DATABASE_PATH']), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'suprajit_system.log')
    
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(file_formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to prevent duplicates during testing
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    app.config['LOG_FILE_PATH'] = log_file


from app.config import get_config
from app.database import get_connection, ensure_schema, GET_USER_BY_ID

# Initialize extensions globally so blueprints can import them

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'error'

def create_app():
    import sys
    if getattr(sys, 'frozen', False):
        # If running as PyInstaller EXE
        template_folder = os.path.join(sys._MEIPASS, 'app', 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'app', 'static')
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        app = Flask(__name__)
    cfg = get_config()
    
    # Load config into Flask app
    app.config.from_object(cfg)
    
    setup_logging(app)
    
    # Initialize Extensions
    
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # User Loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        # We need a quick DB connection just for loading the session
        conn = get_connection(app.config['DATABASE_PATH'])
        row = conn.execute(GET_USER_BY_ID, (user_id,)).fetchone()
        conn.close()
        if not row:
            return None
            
        from app.auth_models import User
        return User(row)

    # Request-Scoped Database Connection
    @app.before_request
    def before_request():
        # Every request gets a fresh DB connection stored in `g`
        g.db = get_connection(app.config['DATABASE_PATH'])

    @app.teardown_request
    def teardown_request(exception):
        # Always close it when the request is done
        db = getattr(g, 'db', None)
        if db is not None:
            db.close()

    # Blueprints (Routes)
    from app.routes.auth import auth_bp
    from app.routes.portal import portal_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')



    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    
    # Initialize Database Schema
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)
    with app.app_context():
        conn = get_connection(app.config['DATABASE_PATH'])
        ensure_schema(conn)
        
        # Security: Enforce unique cryptographically secure secret key per installation
        secret_row = conn.execute("SELECT value FROM system_settings WHERE key = 'secret_key'").fetchone()
        if not secret_row:
            import secrets
            new_secret = secrets.token_hex(32)
            conn.execute("INSERT INTO system_settings (key, value) VALUES ('secret_key', ?)", (new_secret,))
            conn.commit()
            app.config['SECRET_KEY'] = new_secret
        else:
            app.config['SECRET_KEY'] = secret_row['value']
            
        # Ensure at least one admin exists for completely fresh installs
        admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        if admin_count == 0:
            from werkzeug.security import generate_password_hash
            default_pass = generate_password_hash('admin123')
            conn.execute("INSERT INTO users (username, password_hash, display_name, role) VALUES ('bootstrap_admin', ?, 'Administrator', 'admin')", (default_pass,))
            conn.commit()
            
        conn.close()

    # Global Rigorous Error Handler
    @app.errorhandler(Exception)
    def handle_global_exception(e):
        import traceback
        import sys
        from flask import render_template
        from werkzeug.exceptions import HTTPException
        
        # Pass through normal HTTP aborts (like 401 Unauthorized or 404 Not Found) without a terrifying traceback
        if isinstance(e, HTTPException):
            return e
            
        # For actual server crashes (500s), print the traceback to the terminal
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
            
        error_msg = str(e)
        return render_template('errors/500.html', error_msg=error_msg), 500

    # Start the internal background scheduler
    from app.scheduler import start_background_scheduler
    start_background_scheduler(app)

    return app


