@echo off
echo ===================================================
echo   Suprajit Quality Portal - Service Uninstaller
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
set NSSM_EXE=%APP_DIR%nssm\win64\nssm.exe
set SERVICE_NAME=SuprajitQualityPortal

if not exist "%NSSM_EXE%" (
    echo Error: NSSM not found. The service might not be installed.
    pause
    exit /b 1
)

echo Stopping the service...
"%NSSM_EXE%" stop %SERVICE_NAME%

echo Removing the service...
"%NSSM_EXE%" remove %SERVICE_NAME% confirm

echo Removing Windows Firewall rule...
netsh advfirewall firewall delete rule name="Suprajit Portal" >nul 2>&1

echo.
echo ===================================================
echo   SUCCESS! The service has been completely removed.
echo ===================================================
pause
