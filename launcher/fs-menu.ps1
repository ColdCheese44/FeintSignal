<#
  FeintSignal Terminal Menu - classic text-mode launcher and WPF fallback.
  Starts the backend/frontend silently, runs the pipeline, and reports live status.
#>
param(
  [string[]]$TestInputs,
  [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPort = 8765
$FrontendPort = 5173

function Get-LauncherLogPath { return Join-Path $PSScriptRoot "launcher.log" }

function Write-LauncherLog([string]$Action) {
  Add-Content -LiteralPath (Get-LauncherLogPath) -Value "$(Get-Date -Format s) $Action"
}

function Test-Port([int]$Port) {
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
    $ok = $async.AsyncWaitHandle.WaitOne(400)
    $connected = $ok -and $client.Connected
    $client.Close()
    return $connected
  } catch { return $false }
}

function Get-Pythonw {
  $pyw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
  $py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  if (Test-Path -LiteralPath $pyw) { return $pyw }
  if (Test-Path -LiteralPath $py) { return $py }
  return "py"
}

function Get-PythonConsole {
  $py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  if (Test-Path -LiteralPath $py) { return $py }
  return "py"
}

function Start-Backend {
  if (Test-Port $BackendPort) { return }
  $logDir = Join-Path $ProjectRoot "logs"
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  Start-Process -FilePath (Get-Pythonw) -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "$BackendPort") `
    -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardError (Join-Path $logDir "backend.log") `
    -RedirectStandardOutput (Join-Path $logDir "backend.out.log") | Out-Null
}

function Start-Frontend {
  if (Test-Port $FrontendPort) { return }
  $frontend = Join-Path $ProjectRoot "frontend"
  $logDir = Join-Path $ProjectRoot "logs"
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $cmd = "Set-Location -LiteralPath '$frontend'; npm run dev -- --host 127.0.0.1 --port $FrontendPort"
  Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", $cmd) `
    -WorkingDirectory $frontend -WindowStyle Hidden -RedirectStandardError (Join-Path $logDir "frontend.err.log") `
    -RedirectStandardOutput (Join-Path $logDir "frontend.log") | Out-Null
}

function Stop-Stack {
  $procs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*uvicorn*backend.main*' })
  $procs += @(Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*vite*' -and $_.CommandLine -like '*FeintSignal*' })
  foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
  return $procs.Count
}

function Show-Banner {
  $host.UI.RawUI.WindowTitle = "FEINTSIGNAL $([char]0x2014) Intelligence Dashboard"
  Clear-Host
  $backend = if (Test-Port $BackendPort) { "UP" } else { "DOWN" }
  $frontend = if (Test-Port $FrontendPort) { "UP" } else { "DOWN" }
  $feintcon = "-"
  if ($backend -eq "UP") {
    try { $feintcon = "FEINTCON " + (Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/system/feintcon" -TimeoutSec 1).level } catch { }
  }
  Write-Host "==================================================" -ForegroundColor Cyan
  Write-Host "  F E I N T S I G N A L" -ForegroundColor Cyan
  Write-Host "  Local-first current-affairs intelligence" -ForegroundColor DarkCyan
  Write-Host "==================================================" -ForegroundColor Cyan
  Write-Host ("  Backend: {0,-5}  Frontend: {1,-5}  {2}" -f $backend, $frontend, $feintcon) -ForegroundColor Green
  Write-Host "  FEINTCON is an internal indicator, not official DEFCON." -ForegroundColor DarkGray
  Write-Host ""
}

$script:TestInputQueue = @($TestInputs)
function Get-NextChoice {
  if ($script:TestInputQueue.Count -gt 0) {
    $choice = $script:TestInputQueue[0]
    $script:TestInputQueue = if ($script:TestInputQueue.Count -gt 1) { @($script:TestInputQueue[1..($script:TestInputQueue.Count - 1)]) } else { @() }
    Write-Host "Selected (test): $choice" -ForegroundColor DarkGreen
    return $choice
  }
  return Read-Host "Choose an action"
}

function Pause-IfNeeded {
  if ($NoPause -or $script:TestInputQueue.Count -gt 0) { return }
  [void](Read-Host "Press Enter to continue")
}

while ($true) {
  Show-Banner
  Write-Host "[1] Start stack (backend + frontend, hidden)"
  Write-Host "[2] Open dashboard (app window)"
  Write-Host "[3] Seed mock data"
  Write-Host "[4] Run pipeline once"
  Write-Host "[5] Run tests (pytest)"
  Write-Host "[6] Stop all background processes"
  Write-Host "[7] View launcher log"
  Write-Host "[0] Exit"
  Write-Host ""

  $choice = Get-NextChoice
  $shouldExit = $false
  switch ($choice) {
    "1" { Write-LauncherLog "Start stack"; Start-Backend; Start-Frontend; Write-Host "Stack starting silently..." -ForegroundColor Green; Pause-IfNeeded }
    "2" { Write-LauncherLog "Open dashboard"; & (Join-Path $PSScriptRoot "fs-terminal.ps1"); Pause-IfNeeded }
    "3" { Write-LauncherLog "Seed"; Push-Location $ProjectRoot; try { & (Get-PythonConsole) "scripts\seed_mock_data.py" } finally { Pop-Location }; Pause-IfNeeded }
    "4" { Write-LauncherLog "Run pipeline"; Push-Location $ProjectRoot; try { & (Get-PythonConsole) "scripts\hourly_update.py" } finally { Pop-Location }; Pause-IfNeeded }
    "5" { Write-LauncherLog "Tests"; Push-Location $ProjectRoot; try { & (Get-PythonConsole) "-m" "pytest" "backend/tests" "-q" } finally { Pop-Location }; Pause-IfNeeded }
    "6" { Write-LauncherLog "Stop all"; $n = Stop-Stack; Write-Host "Stopped $n process(es)." -ForegroundColor Yellow; Pause-IfNeeded }
    "7" { $log = Get-LauncherLogPath; if (Test-Path $log) { Get-Content -LiteralPath $log -Tail 25 } else { Write-Host "No launcher log yet." -ForegroundColor Yellow }; Pause-IfNeeded }
    "0" { Write-LauncherLog "Exit"; $shouldExit = $true }
    default { Write-Host "Unknown option." -ForegroundColor Yellow; Pause-IfNeeded }
  }

  # 'break' inside a switch only exits the switch; use a flag to leave the while loop.
  if ($shouldExit) { break }
}
