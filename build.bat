@echo off
echo Cleaning old builds...
rmdir /s /q build dist

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Building executable...
pyinstaller SuprajitQualityPortal.spec --noconfirm

echo Copying configuration templates and deployment scripts...
copy .env.example dist\SuprajitQualityPortal\.env.example
copy install_service.bat dist\SuprajitQualityPortal\install_service.bat
copy uninstall_service.bat dist\SuprajitQualityPortal\uninstall_service.bat
mkdir dist\SuprajitQualityPortal\service
copy service\nssm.exe dist\SuprajitQualityPortal\service\nssm.exe

echo Build complete! The results are available in: %CD%\dist
