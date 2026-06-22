<#
  Installs / removes the FeintSignal background automation as Windows Scheduled Tasks.
  These run silently through a hidden PowerShell wrapper under the current user.

    .\scripts\install-autostart.ps1 -Install                 # hourly pipeline updater
    .\scripts\install-autostart.ps1 -Install -StartBackendAtLogon
    .\scripts\install-autostart.ps1 -Install -IntervalMinutes 30
    .\scripts\install-autostart.ps1 -Uninstall

  No live research, no LLM, no Discord sending is enabled by this task - it only runs the
  local deterministic pipeline against mock data and refreshes the SQLite store.
#>
param(
  [switch]$Install,
  [switch]$Uninstall,
  [switch]$StartBackendAtLogon,
  [int]$IntervalMinutes = 60
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$UpdateTaskName = "FeintSignal Hourly Update"
$BackendTaskName = "FeintSignal Backend (logon)"
$Runner = Join-Path $PSScriptRoot "run-background.ps1"
$PowerShell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

function Remove-TaskIfPresent([string]$name) {
  $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if ($existing) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Host "Removed task: $name"
  }
}

if ($Uninstall) {
  Remove-TaskIfPresent $UpdateTaskName
  Remove-TaskIfPresent $BackendTaskName
  Write-Host "FeintSignal background automation removed."
  return
}

if (-not $Install) {
  Write-Host "Specify -Install or -Uninstall. See the comment header for options." -ForegroundColor Yellow
  return
}

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
  Write-Host "WARNING: no .venv found - the task will use the system Python launcher." -ForegroundColor Yellow
  Write-Host "         Create it first:  py -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt" -ForegroundColor Yellow
}

# --- Hourly pipeline updater (silent) ---
Remove-TaskIfPresent $UpdateTaskName
$updateArgs = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`" -Task Hourly"
$updateAction = New-ScheduledTaskAction -Execute $PowerShell -Argument $updateArgs -WorkingDirectory $ProjectRoot
$updateTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $UpdateTaskName -Action $updateAction -Trigger $updateTrigger -Settings $settings -Principal $principal -Description "FeintSignal: run the local intelligence pipeline every $IntervalMinutes minutes (silent, mock data)." | Out-Null
Write-Host "Installed task '$UpdateTaskName' - runs every $IntervalMinutes minute(s), hidden."

# --- Optional: start the backend silently at logon so the dashboard is always available ---
if ($StartBackendAtLogon) {
  Remove-TaskIfPresent $BackendTaskName
  $backendArgs = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`" -Task Backend"
  $backendAction = New-ScheduledTaskAction -Execute $PowerShell -Argument $backendArgs -WorkingDirectory $ProjectRoot
  $backendTrigger = New-ScheduledTaskTrigger -AtLogOn
  $backendSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
  Register-ScheduledTask -TaskName $BackendTaskName -Action $backendAction -Trigger $backendTrigger -Settings $backendSettings -Principal $principal -Description "FeintSignal: start the FastAPI backend silently at logon." | Out-Null
  Write-Host "Installed task '$BackendTaskName' - starts the backend hidden at logon."
}

# Run one update now so there is fresh data immediately.
Start-Process -FilePath $PowerShell -ArgumentList @("-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", $Runner, "-Task", "Hourly") `
  -WorkingDirectory $ProjectRoot -WindowStyle Hidden | Out-Null
Write-Host "Kicked off an initial pipeline run. Done."
