$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\Users\7make\.claude\toast.ps1`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(3)
Register-ScheduledTask -TaskName "ClaudeToastTest" -Action $action -Trigger $trigger -Force | Out-Null
Write-Host "Task created, will run in 3 seconds"
