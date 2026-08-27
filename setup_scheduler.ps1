# Must be run as Administrator
$TaskName = "Suprajit_N1_Batch_Ingestion"
$ActionExe = "C:\Users\humza\suprajit_v2\.venv\Scripts\python.exe"
$ActionArg = "C:\Users\humza\suprajit_v2\ingest_batch.py"
$WorkingDir = "C:\Users\humza\suprajit_v2"

Write-Host "Creating Scheduled Task: $TaskName"

$Action = New-ScheduledTaskAction -Execute $ActionExe -Argument $ActionArg -WorkingDirectory $WorkingDir

# Run daily at 2:00 AM
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# Run whether user is logged on or not, with highest privileges
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

Write-Host "Done! The database will now sync automatically every night at 2:00 AM."
