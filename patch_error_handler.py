# -*- coding: utf-8 -*-
import io

with io.open(r'C:\Users\humza\suprajit_v2\app\__init__.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''    # Global Rigorous Error Handler
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
            return e'''

replacement = '''    # Global Rigorous Error Handler
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
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)'''

c = c.replace(target, replacement)

with io.open(r'C:\Users\humza\suprajit_v2\app\__init__.py', 'w', encoding='utf-8') as f:
    f.write(c)
