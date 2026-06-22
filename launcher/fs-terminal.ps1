<#
  FeintSignal Terminal - opens the dashboard as a chromeless desktop app window (Edge/Chrome --app),
  the FeintTrade-style shell. Starts the backend (FastAPI) and the frontend (Vite) silently first if
  they are not already running, then waits for the dashboard to come up.
#>
param(
  [int]$BackendPort = 8765,
  [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Url = "http://localhost:$FrontendPort"
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

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

# --- Start the backend hidden (pythonw = no console window) if it is not up yet. ---
if (-not (Test-Port $BackendPort)) {
  $pyw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
  $py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  $exe = if (Test-Path -LiteralPath $pyw) { $pyw } elseif (Test-Path -LiteralPath $py) { $py } else { "py" }
  Start-Process -FilePath $exe -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "$BackendPort") `
    -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardError (Join-Path $LogDir "backend.log") `
    -RedirectStandardOutput (Join-Path $LogDir "backend.out.log") | Out-Null
}

# --- Start the frontend dev server hidden if it is not up yet. ---
if (-not (Test-Port $FrontendPort)) {
  $frontend = Join-Path $ProjectRoot "frontend"
  if (-not (Test-Path -LiteralPath (Join-Path $frontend "node_modules"))) {
    # First run: install deps in a visible window so progress is watchable, then start the server.
    $install = "Set-Location -LiteralPath '$frontend'; Write-Host 'Installing frontend dependencies (first run)...' -ForegroundColor Cyan; npm install; Write-Host 'Starting dev server...' -ForegroundColor Green; npm run dev -- --host 127.0.0.1 --port $FrontendPort"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $install) -WorkingDirectory $frontend | Out-Null
  } else {
    $cmd = "Set-Location -LiteralPath '$frontend'; npm run dev -- --host 127.0.0.1 --port $FrontendPort"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", $cmd) `
      -WorkingDirectory $frontend -WindowStyle Hidden -RedirectStandardError (Join-Path $LogDir "frontend.err.log") `
      -RedirectStandardOutput (Join-Path $LogDir "frontend.log") | Out-Null
  }
}

# --- Wait for the dashboard to be reachable (up to ~40s for a cold first run). ---
for ($i = 0; $i -lt 80; $i++) {
  if ((Test-Port $BackendPort) -and (Test-Port $FrontendPort)) { break }
  Start-Sleep -Milliseconds 500
}

if (-not (Test-Port $BackendPort) -or -not (Test-Port $FrontendPort)) {
  throw "FeintSignal stack did not become ready. Check logs\backend.log and logs\frontend.err.log."
}

# --- Open as a chromeless app window. Prefer Edge, then Chrome, then default browser. ---
$candidates = @(
  (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
  (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
  (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
  (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe")
)
$browser = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if ($browser) {
  # A dedicated user-data-dir gives the app window its own identity and taskbar entry.
  $profileDir = Join-Path $env:LOCALAPPDATA "FeintSignalTerminal"
  Start-Process -FilePath $browser -ArgumentList @(
    "--app=$Url",
    "--window-size=1480,920",
    "--user-data-dir=$profileDir"
  ) | Out-Null
  Write-Host "FeintSignal dashboard opened ($([System.IO.Path]::GetFileName($browser)) app window) at $Url"
} else {
  Start-Process $Url | Out-Null
  Write-Host "No Edge/Chrome found; opened $Url in the default browser."
}
