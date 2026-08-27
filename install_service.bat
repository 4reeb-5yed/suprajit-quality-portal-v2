@echo off
echo ===================================================
echo   Suprajit Quality Portal - Service Installer
echo ===================================================
echo.

:: Request Admin Privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Administrator privileges confirmed.
) else (
    echo Failure: Please right-click and run this script as Administrator.
    pause
    exit /b 1
)

set APP_DIR=%~dp0
set PYTHON_EXE=%APP_DIR%.venv\Scripts\python.exe
set SCRIPT_PATH=%APP_DIR%web_server.py
set SERVICE_NAME=SuprajitQualityPortal

:: Check if Python venv exists
if not exist "%PYTHON_EXE%" (
    echo Error: Python virtual environment not found. 
    echo Please ensure the .venv folder is included.
    pause
    exit /b 1
)

:: Download NSSM (Non-Sucking Service Manager) if not present
set NSSM_URL=https://nssm.cc/release/nssm-2.24.zip
set NSSM_DIR=%APP_DIR%nssm
set NSSM_EXE=%NSSM_DIR%\win64\nssm.exe

if not exist "%NSSM_EXE%" (
    echo Downloading NSSM Service Manager...
    mkdir "%NSSM_DIR%" 2>nul
    powershell -Command "Invoke-WebRequest -Uri '%NSSM_URL%' -OutFile '%APP_DIR%nssm.zip'"
    powershell -Command "Expand-Archive -Path '%APP_DIR%nssm.zip' -DestinationPath '%APP_DIR%nssm_temp' -Force"
    xcopy /E /Y /I "%APP_DIR%nssm_temp\nssm-2.24\win64" "%NSSM_DIR%\win64"
    rmdir /S /Q "%APP_DIR%nssm_temp"
    del "%APP_DIR%nssm.zip"
)

:: Stop existing service if it exists
"%NSSM_EXE%" stop %SERVICE_NAME% >nul 2>&1
"%NSSM_EXE%" remove %SERVICE_NAME% confirm >nul 2>&1

echo.
echo Installing %SERVICE_NAME% as a Windows Service...
"%NSSM_EXE%" install %SERVICE_NAME% "%PYTHON_EXE%" "%SCRIPT_PATH%"
"%NSSM_EXE%" set %SERVICE_NAME% AppDirectory "%APP_DIR%"
"%NSSM_EXE%" set %SERVICE_NAME% DisplayName "Suprajit Quality Data Portal"
"%NSSM_EXE%" set %SERVICE_NAME% Description "Runs the internal factory web portal for N-1 Excel ingestion and search."
"%NSSM_EXE%" set %SERVICE_NAME% Start SERVICE_AUTO_START

echo Starting the service...
"%NSSM_EXE%" start %SERVICE_NAME%

echo.
echo Opening Windows Firewall for Port 5000...
netsh advfirewall firewall add rule name="Suprajit Portal" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1

echo.
echo ===================================================
echo   SUCCESS! 
echo   The Suprajit Portal is now running in the background.
echo   It will automatically start whenever the PC boots.
echo   
echo   Factory PCs can access it at: http://localhost:5000
echo ===================================================
pause
