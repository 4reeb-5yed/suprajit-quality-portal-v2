with open('app/__init__.py', 'r') as f:
    c = f.read()

handler_code = '''    # Global Rigorous Error Handler
    @app.errorhandler(Exception)
    def handle_global_exception(e):
        import traceback
        import sys
        from flask import render_template
        from werkzeug.exceptions import HTTPException
        
        # Log exactly what happened to the server terminal
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
        
        # Pass through normal HTTP aborts (like 401 Unauthorized or 404 Not Found)
        if isinstance(e, HTTPException):
            return e
            
        error_msg = str(e)
        return render_template('errors/500.html', error_msg=error_msg), 500

    # Start the internal background scheduler'''

c = c.replace('    # Start the internal background scheduler', handler_code)

with open('app/__init__.py', 'w') as f:
    f.write(c)
