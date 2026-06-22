<#
  FeintSignal Control Panel - native WPF desktop app for the FeintSignal intelligence dashboard.
  Launches the backend (FastAPI) and frontend (Vite) silently in the background, opens the
  dashboard as a chromeless app window, runs the pipeline, and shows live status.
  No external dependencies (uses WPF built into Windows). Falls back to the terminal menu if WPF is unavailable.

  Mirrors the FeintTrade / FeintSupplyCo launcher convention.
#>

# WPF needs a single-threaded apartment; relaunch under -STA hidden if we are not already there.
# (Skipped during self-test, which only builds the UI tree and never shows the window.)
if (-not $env:FS_APP_SELFTEST -and [System.Threading.Thread]::CurrentThread.GetApartmentState() -ne [System.Threading.ApartmentState]::STA) {
  Start-Process -FilePath "powershell.exe" -ArgumentList @("-STA", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", $PSCommandPath)
  return
}

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$TuiPs1 = Join-Path $PSScriptRoot "fs-menu.ps1"
$TerminalPs1 = Join-Path $PSScriptRoot "fs-terminal.ps1"
$AutostartPs1 = Join-Path $ProjectRoot "scripts\install-autostart.ps1"
$IconPath = Join-Path $PSScriptRoot "fs.ico"
$BackendPort = 8765
$FrontendPort = 5173

try {
  Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Xaml
} catch {
  # WPF unavailable - fall back to the terminal menu.
  Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", $TuiPs1) -WorkingDirectory $ProjectRoot
  return
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function New-Brush([string]$hex) { return New-Object System.Windows.Media.SolidColorBrush ([System.Windows.Media.ColorConverter]::ConvertFromString($hex)) }

$Colors = @{
  Bg     = "#0A0E14"
  Panel  = "#11161F"
  Card   = "#1D2735"
  Text   = "#E6EDF3"
  Muted  = "#647387"
  Green  = "#3FB950"
  Cyan   = "#4F9FE0"
  Amber  = "#E0A317"
  Danger = "#E5484D"
  Border = "#283447"
}

function Set-Output([string]$message, [string]$kind = "info") {
  $brush = switch ($kind) {
    "ok"   { New-Brush $Colors.Green }
    "warn" { New-Brush $Colors.Amber }
    "err"  { New-Brush $Colors.Danger }
    default { New-Brush $Colors.Muted }
  }
  $script:OutputText.Foreground = $brush
  $script:OutputText.Text = "$(Get-Date -Format 'HH:mm:ss')  $message"
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

function Get-Api([string]$path) {
  try { return Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort$path" -TimeoutSec 1 -ErrorAction Stop } catch { return $null }
}

function Get-PythonExe {
  $pyw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
  $py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  if (Test-Path -LiteralPath $pyw) { return @{ Hidden = $pyw; Console = $py } }
  if (Test-Path -LiteralPath $py) { return @{ Hidden = $py; Console = $py } }
  return @{ Hidden = "py"; Console = "py" }   # system fallback (uvicorn must be installed)
}

function Get-BackendProcesses {
  return @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like '*uvicorn*backend.main*' })
}

function Get-FrontendProcesses {
  return @(Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like '*vite*' -and $_.CommandLine -like '*FeintSignal*' })
}

# Starts the FastAPI backend with pythonw.exe (no console window at all).
# Output is redirected to logs\backend*.log so pythonw has valid streams (uvicorn logs to stderr).
function Start-BackendHidden {
  if ((Get-BackendProcesses).Count -gt 0 -or (Test-Port $BackendPort)) { return $false }
  $py = Get-PythonExe
  $logDir = Join-Path $ProjectRoot "logs"
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $args = @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "$BackendPort")
  Start-Process -FilePath $py.Hidden -ArgumentList $args -WorkingDirectory $ProjectRoot -WindowStyle Hidden `
    -RedirectStandardError (Join-Path $logDir "backend.log") -RedirectStandardOutput (Join-Path $logDir "backend.out.log") | Out-Null
  return $true
}

# Starts the Vite dev server hidden. Installs node deps first (visible) if missing.
function Start-FrontendHidden {
  if ((Get-FrontendProcesses).Count -gt 0 -or (Test-Port $FrontendPort)) { return $false }
  $frontend = Join-Path $ProjectRoot "frontend"
  if (-not (Test-Path -LiteralPath (Join-Path $frontend "node_modules"))) {
    $install = "Set-Location -LiteralPath '$frontend'; Write-Host 'Installing frontend dependencies (first run)...' -ForegroundColor Cyan; npm install; Write-Host 'Starting dev server...' -ForegroundColor Green; npm run dev -- --host 127.0.0.1 --port $FrontendPort"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $install) -WorkingDirectory $frontend | Out-Null
    return $true
  }
  $logDir = Join-Path $ProjectRoot "logs"
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $cmd = "Set-Location -LiteralPath '$frontend'; npm run dev -- --host 127.0.0.1 --port $FrontendPort"
  Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", $cmd) `
    -WorkingDirectory $frontend -WindowStyle Hidden -RedirectStandardError (Join-Path $logDir "frontend.err.log") `
    -RedirectStandardOutput (Join-Path $logDir "frontend.log") | Out-Null
  return $true
}

function Stop-Stack {
  $procs = @(Get-BackendProcesses) + @(Get-FrontendProcesses)
  foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
  return $procs.Count
}

# Runs a Python entry point in its own visible window so output stays watchable.
function Start-PyWindow([string]$scriptArgs, [string]$label) {
  $py = (Get-PythonExe).Console
  $cmd = "Set-Location -LiteralPath '$ProjectRoot'; Write-Host 'FeintSignal > $label' -ForegroundColor Green; & '$py' $scriptArgs; Write-Host ''; Read-Host 'Press Enter to close'"
  Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd) -WorkingDirectory $ProjectRoot | Out-Null
  Set-Output "Launched: $label" "ok"
}

function Update-Status {
  $backend = (Test-Port $BackendPort)
  $script:BackendValue.Text = if ($backend) { "UP :$BackendPort" } else { "DOWN" }
  $script:BackendValue.Foreground = if ($backend) { New-Brush $Colors.Green } else { New-Brush $Colors.Muted }

  $frontend = (Test-Port $FrontendPort)
  $script:FrontendValue.Text = if ($frontend) { "UP :$FrontendPort" } else { "DOWN" }
  $script:FrontendValue.Foreground = if ($frontend) { New-Brush $Colors.Green } else { New-Brush $Colors.Muted }

  if ($backend) {
    $fc = Get-Api "/system/feintcon"
    if ($fc) {
      $script:FeintconValue.Text = "FEINTCON $($fc.level)"
      $script:FeintconValue.Foreground = New-Brush ($(switch ([int]$fc.level) { 1 { $Colors.Danger } 2 { $Colors.Amber } 3 { $Colors.Amber } 4 { $Colors.Cyan } default { $Colors.Green } }))
    } else { $script:FeintconValue.Text = "..."; $script:FeintconValue.Foreground = New-Brush $Colors.Muted }

    $health = Get-Api "/health"
    $discord = $false
    if ($health -and $health.config) { $discord = [bool]$health.config.enable_discord_send }
    $script:DiscordValue.Text = if ($discord) { "SEND ON" } else { "OFF" }
    $script:DiscordValue.Foreground = if ($discord) { New-Brush $Colors.Amber } else { New-Brush $Colors.Muted }
  } else {
    $script:FeintconValue.Text = "-"; $script:FeintconValue.Foreground = New-Brush $Colors.Muted
    $script:DiscordValue.Text = "-"; $script:DiscordValue.Foreground = New-Brush $Colors.Muted
  }
}

# ---------------------------------------------------------------------------
# Component actions
# ---------------------------------------------------------------------------

function Invoke-Component([string]$key) {
  try {
    switch ($key) {
      "dashboard" {
        Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", $TerminalPs1) -WorkingDirectory $ProjectRoot | Out-Null
        Set-Output "Opening FeintSignal dashboard (app window); starting backend + frontend if needed..." "ok"
      }
      "start-stack" {
        $b = Start-BackendHidden
        $f = Start-FrontendHidden
        Set-Output "Stack starting silently (backend: $([bool]$b), frontend: $([bool]$f))." "ok"
      }
      "start-backend" {
        if (Start-BackendHidden) { Set-Output "Backend started hidden on :$BackendPort." "ok" } else { Set-Output "Backend already running on :$BackendPort." "warn" }
      }
      "start-frontend" {
        if (Start-FrontendHidden) { Set-Output "Frontend dev server started on :$FrontendPort." "ok" } else { Set-Output "Frontend already running on :$FrontendPort." "warn" }
      }
      "stop-all" {
        $n = Stop-Stack
        if ($n -gt 0) { Set-Output "Stopped $n background process(es)." "ok" } else { Set-Output "No FeintSignal processes were running." "warn" }
      }
      "seed"         { Start-PyWindow "scripts\seed_mock_data.py" "Seed mock data" }
      "run-pipeline" { Start-PyWindow "scripts\hourly_update.py" "Run pipeline once" }
      "tests"        { Start-PyWindow "-m pytest backend/tests -q" "pytest backend/tests" }
      "apidocs" {
        Start-BackendHidden | Out-Null
        for ($i = 0; $i -lt 20; $i++) { if (Test-Port $BackendPort) { break }; Start-Sleep -Milliseconds 300 }
        Start-Process "http://127.0.0.1:$BackendPort/docs" | Out-Null
        Set-Output "Opened API docs (/docs)." "ok"
      }
      "install-autostart" {
        $cmd = "Set-Location -LiteralPath '$ProjectRoot'; & '$AutostartPs1' -Install; Write-Host ''; Read-Host 'Press Enter to close'"
        Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd) -WorkingDirectory $ProjectRoot | Out-Null
        Set-Output "Installing hourly background updater (Task Scheduler)..." "ok"
      }
      "remove-autostart" {
        $cmd = "Set-Location -LiteralPath '$ProjectRoot'; & '$AutostartPs1' -Uninstall; Write-Host ''; Read-Host 'Press Enter to close'"
        Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd) -WorkingDirectory $ProjectRoot | Out-Null
        Set-Output "Removing background updater autostart..." "ok"
      }
      "tui"          { Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $TuiPs1) -WorkingDirectory $ProjectRoot | Out-Null; Set-Output "Opened terminal menu." "ok" }
      "logs"         { $log = Join-Path $PSScriptRoot "launcher.log"; if (Test-Path $log) { Start-Process $log } else { Set-Output "No launcher.log yet." "warn" } }
      "data-folder"  { Start-Process (Join-Path $ProjectRoot "data") | Out-Null; Set-Output "Opened data folder." "ok" }
      "project"      { Start-Process $ProjectRoot | Out-Null; Set-Output "Opened project folder." "ok" }
      "env-example"  { Start-Process (Join-Path $ProjectRoot ".env.example") | Out-Null; Set-Output "Opened .env.example (template only)." "ok" }
      default        { Set-Output "Unknown action: $key" "warn" }
    }
    if ($key -in @("start-stack", "start-backend", "start-frontend", "stop-all", "dashboard")) { Start-Sleep -Milliseconds 500; Update-Status }
  } catch {
    Set-Output "Error: $($_.Exception.Message)" "err"
  }
}

# ---------------------------------------------------------------------------
# UI construction
# ---------------------------------------------------------------------------

$window = New-Object System.Windows.Window
$window.Title = "FEINTSIGNAL - Intelligence Dashboard Control Panel"
$window.Width = 760
$window.Height = 600
$window.WindowStartupLocation = "CenterScreen"
$window.Background = New-Brush $Colors.Bg
$window.FontFamily = New-Object System.Windows.Media.FontFamily("Segoe UI")
if (Test-Path -LiteralPath $IconPath) {
  try { $window.Icon = New-Object System.Windows.Media.Imaging.BitmapImage ([Uri]$IconPath) } catch { }
}

$root = New-Object System.Windows.Controls.DockPanel
$root.Margin = "16"

# --- Header ---
$header = New-Object System.Windows.Controls.StackPanel
[System.Windows.Controls.DockPanel]::SetDock($header, "Top")
$title = New-Object System.Windows.Controls.TextBlock
$title.Text = "F E I N T S I G N A L"
$title.FontSize = 24
$title.FontWeight = "Bold"
$title.Foreground = New-Brush $Colors.Cyan
$subtitle = New-Object System.Windows.Controls.TextBlock
$subtitle.Text = "Local-first current-affairs intelligence - control panel"
$subtitle.FontSize = 12
$subtitle.Foreground = New-Brush $Colors.Muted
$subtitle.Margin = "0,0,0,12"
$header.AddChild($title)
$header.AddChild($subtitle)

# --- Status bar ---
function New-StatusCell([string]$label) {
  $sp = New-Object System.Windows.Controls.StackPanel
  $sp.Margin = "0,0,28,0"
  $l = New-Object System.Windows.Controls.TextBlock
  $l.Text = $label; $l.FontSize = 10; $l.Foreground = New-Brush $Colors.Muted
  $v = New-Object System.Windows.Controls.TextBlock
  $v.Text = "..."; $v.FontSize = 14; $v.FontWeight = "Bold"; $v.Foreground = New-Brush $Colors.Text
  $sp.AddChild($l); $sp.AddChild($v)
  return @{ Panel = $sp; Value = $v }
}

$statusBar = New-Object System.Windows.Controls.Border
$statusBar.Background = New-Brush $Colors.Panel
$statusBar.BorderBrush = New-Brush $Colors.Border
$statusBar.BorderThickness = "1"
$statusBar.CornerRadius = "6"
$statusBar.Padding = "14,10"
$statusBar.Margin = "0,0,0,14"
[System.Windows.Controls.DockPanel]::SetDock($statusBar, "Top")
$statusInner = New-Object System.Windows.Controls.StackPanel
$statusInner.Orientation = "Horizontal"

$cellBackend = New-StatusCell "BACKEND";   $script:BackendValue = $cellBackend.Value
$cellFrontend = New-StatusCell "FRONTEND"; $script:FrontendValue = $cellFrontend.Value
$cellFeintcon = New-StatusCell "READINESS"; $script:FeintconValue = $cellFeintcon.Value
$cellDiscord = New-StatusCell "DISCORD";   $script:DiscordValue = $cellDiscord.Value
$statusInner.AddChild($cellBackend.Panel)
$statusInner.AddChild($cellFrontend.Panel)
$statusInner.AddChild($cellFeintcon.Panel)
$statusInner.AddChild($cellDiscord.Panel)

$refreshBtn = New-Object System.Windows.Controls.Button
$refreshBtn.Content = "Refresh"
$refreshBtn.Padding = "12,4"
$refreshBtn.Background = New-Brush $Colors.Card
$refreshBtn.Foreground = New-Brush $Colors.Cyan
$refreshBtn.BorderBrush = New-Brush $Colors.Border
$refreshBtn.Cursor = "Hand"
$refreshBtn.VerticalAlignment = "Center"
$refreshBtn.Add_Click({ Update-Status; Set-Output "Status refreshed." "info" })
$statusInner.AddChild($refreshBtn)
$statusBar.Child = $statusInner

# --- Output line (bottom) ---
$outputBorder = New-Object System.Windows.Controls.Border
$outputBorder.Background = New-Brush $Colors.Panel
$outputBorder.BorderBrush = New-Brush $Colors.Border
$outputBorder.BorderThickness = "1"
$outputBorder.CornerRadius = "6"
$outputBorder.Padding = "12,8"
$outputBorder.Margin = "0,12,0,0"
[System.Windows.Controls.DockPanel]::SetDock($outputBorder, "Bottom")
$script:OutputText = New-Object System.Windows.Controls.TextBlock
$script:OutputText.Text = "Ready. FEINTCON is an internal indicator, not official DEFCON."
$script:OutputText.TextWrapping = "Wrap"
$script:OutputText.Foreground = New-Brush $Colors.Muted
$script:OutputText.FontFamily = New-Object System.Windows.Media.FontFamily("Consolas")
$script:OutputText.FontSize = 12
$outputBorder.Child = $script:OutputText

# --- Sections with buttons ---
$scroll = New-Object System.Windows.Controls.ScrollViewer
$scroll.VerticalScrollBarVisibility = "Auto"
$content = New-Object System.Windows.Controls.StackPanel

function New-ActionButton([string]$text, [string]$key, [string]$kind, [string]$tip) {
  $b = New-Object System.Windows.Controls.Button
  $b.Content = $text
  $b.Tag = $key
  $b.Width = 222
  $b.Height = 40
  $b.Margin = "0,0,10,10"
  $b.Cursor = "Hand"
  $b.HorizontalContentAlignment = "Left"
  $b.Padding = "12,0"
  $b.FontSize = 13
  $b.Background = New-Brush $Colors.Card
  $b.BorderThickness = "1"
  $b.ToolTip = $tip
  $accent = switch ($kind) {
    "green"  { $Colors.Green }
    "cyan"   { $Colors.Cyan }
    "danger" { $Colors.Danger }
    "amber"  { $Colors.Amber }
    default  { $Colors.Border }
  }
  $b.BorderBrush = New-Brush $accent
  $b.Foreground = New-Brush $Colors.Text
  $b.Add_Click({ Invoke-Component $this.Tag })
  return $b
}

function Add-Section([string]$heading, [array]$buttons) {
  $h = New-Object System.Windows.Controls.TextBlock
  $h.Text = $heading.ToUpper()
  $h.FontSize = 12
  $h.FontWeight = "Bold"
  $h.Foreground = New-Brush $Colors.Cyan
  $h.Margin = "0,6,0,8"
  $content.AddChild($h)
  $wrap = New-Object System.Windows.Controls.WrapPanel
  $wrap.Margin = "0,0,0,8"
  foreach ($b in $buttons) { $wrap.AddChild($b) }
  $content.AddChild($wrap)
}

Add-Section "Dashboard & Stack" @(
  (New-ActionButton "Open Dashboard"      "dashboard"      "green"  "Open the dashboard as a chromeless app window (starts backend + frontend silently if needed)"),
  (New-ActionButton "Start Stack"         "start-stack"    "green"  "Start backend + frontend hidden in the background"),
  (New-ActionButton "Start Backend"       "start-backend"  "cyan"   "Start the FastAPI backend hidden (:8765)"),
  (New-ActionButton "Start Frontend"      "start-frontend" "cyan"   "Start the Vite dev server hidden (:5173)"),
  (New-ActionButton "Stop All"            "stop-all"       "danger" "Stop all FeintSignal background processes")
)

Add-Section "Pipeline & Data" @(
  (New-ActionButton "Seed Mock Data"      "seed"         "neutral" "Reset + seed the local SQLite database from mock data"),
  (New-ActionButton "Run Pipeline Now"    "run-pipeline" "neutral" "Run one collect -> score -> FEINTCON -> alerts cycle"),
  (New-ActionButton "Run Tests"           "tests"        "neutral" "Run the pytest backend suite"),
  (New-ActionButton "API Docs"            "apidocs"      "neutral" "Open the FastAPI /docs page")
)

Add-Section "Background Automation" @(
  (New-ActionButton "Install Hourly Updater" "install-autostart" "cyan"   "Register a hidden hourly pipeline task (Task Scheduler)"),
  (New-ActionButton "Remove Hourly Updater"  "remove-autostart"  "danger" "Remove the background updater task")
)

Add-Section "Files & Tools" @(
  (New-ActionButton "Open launcher.log"   "logs"        "neutral" "Open the launcher activity log"),
  (New-ActionButton "Open Data Folder"    "data-folder" "neutral" "Open the data directory"),
  (New-ActionButton "Open Project Folder" "project"     "neutral" "Open the project root"),
  (New-ActionButton "Open .env.example"   "env-example" "neutral" "Open the environment template (no secrets)"),
  (New-ActionButton "Terminal Menu"       "tui"         "neutral" "Open the classic text menu")
)

$scroll.Content = $content

$root.AddChild($header)
$root.AddChild($statusBar)
$root.AddChild($outputBorder)
$root.AddChild($scroll)
$window.Content = $root

Update-Status
$window.Add_ContentRendered({ Update-Status })

if ($env:FS_APP_SELFTEST -eq "1") {
  Write-Host "SELFTEST OK: window built ($($content.Children.Count) sections), backend=$($script:BackendValue.Text), frontend=$($script:FrontendValue.Text), readiness=$($script:FeintconValue.Text), discord=$($script:DiscordValue.Text)"
  return
}

[void]$window.ShowDialog()
