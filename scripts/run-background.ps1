<#
  Hidden Task Scheduler entry point. Keeps Python stdout/stderr valid by
  redirecting both streams to git-ignored log files.
#>
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("Hourly", "Backend")]
  [string]$Task
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "py" }

if ($Task -eq "Hourly") {
  Start-Process -FilePath $python -ArgumentList @("scripts\hourly_update.py") -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden -Wait -RedirectStandardError (Join-Path $LogDir "hourly-update.err.log") `
    -RedirectStandardOutput (Join-Path $LogDir "hourly-update.log")
  return
}

Start-Process -FilePath $python -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8765") `
  -WorkingDirectory $ProjectRoot -WindowStyle Hidden -Wait -RedirectStandardError (Join-Path $LogDir "backend-task.log") `
  -RedirectStandardOutput (Join-Path $LogDir "backend-task.out.log")
