@echo off
echo Building Suprajit Quality Portal Executable...
.\.venv\Scripts\pyinstaller.exe --noconfirm --onedir --console --name "SuprajitQualityPortal" --add-data "app/templates;app/templates" --add-data "app/static;app/static" web_server.py
echo Build complete!
