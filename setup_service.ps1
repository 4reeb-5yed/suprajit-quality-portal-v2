# Must be run as Administrator
$ErrorActionPreference = "Stop"

$ServiceDir = "C:\Users\humza\suprajit_v2\service"
$ExePath = "$ServiceDir\portal-service.exe"

Write-Host "1. Downloading WinSW (Windows Service Wrapper)..."
Invoke-WebRequest -Uri "https://github.com/winsw/winsw/releases/download/v2.12.0/WinSW-x64.exe" -OutFile $ExePath

Write-Host "2. Installing the Suprajit Portal Service..."
Set-Location $ServiceDir
& $ExePath install

Write-Host "3. Starting the Service..."
& $ExePath start

Write-Host "Done! The Web Server is now running in the background and will survive PC reboots."
Write-Host "You can manage it in the Windows 'Services' app under 'Suprajit Quality Portal V2'."
