import re

with open('app/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
    # Path configuration
    import sys
    import os
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller EXE: BASE_DIR is the folder containing the .exe
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        # Running from source
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""

content = re.sub(r"    # Path configuration\s+BASE_DIR = os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)", replacement, content)

with open('app/config.py', 'w', encoding='utf-8') as f:
    f.write(content)
