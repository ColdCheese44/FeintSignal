<#
  Installs Desktop + Start Menu shortcuts for the FeintSignal launcher.
    - "FeintSignal"           -> the WPF control panel (fs-app.ps1), launched hidden/-STA.
    - "FeintSignal Dashboard" -> opens the dashboard as a Brave fullscreen app window (fs-terminal.ps1).
#>
$ErrorActionPreference = "Stop"

function Get-ProjectRoot { return Split-Path -Parent $PSScriptRoot }

function Ensure-Icon {
  $iconPath = Join-Path $PSScriptRoot "fs.ico"
  if (-not (Test-Path -LiteralPath $iconPath)) {
    & (Join-Path $PSScriptRoot "generate-icon.ps1")
  }
  return $iconPath
}

function New-Shortcut {
  param(
    [string]$ShortcutPath,
    [string]$TargetPath,
    [string]$Arguments,
    [string]$WorkingDirectory,
    [string]$IconLocation,
    [string]$Description
  )
  $directory = Split-Path -Parent $ShortcutPath
  if (-not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Path $directory | Out-Null }
  $shell = New-Object -ComObject WScript.Shell
  $shortcut = $shell.CreateShortcut($ShortcutPath)
  $shortcut.TargetPath = $TargetPath
  $shortcut.Arguments = $Arguments
  $shortcut.WorkingDirectory = $WorkingDirectory
  $shortcut.IconLocation = $IconLocation
  $shortcut.WindowStyle = 1
  $shortcut.Description = $Description
  $shortcut.Save()
}

$projectRoot = Get-ProjectRoot
$desktopPath = [Environment]::GetFolderPath("Desktop")
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$iconPath = Ensure-Icon
$powershellPath = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

# Control panel: hidden console behind the GUI, single-threaded apartment for WPF.
$appArgs = "-ExecutionPolicy Bypass -STA -WindowStyle Hidden -File `"$projectRoot\launcher\fs-app.ps1`""
New-Shortcut -ShortcutPath (Join-Path $desktopPath "FeintSignal.lnk") -TargetPath $powershellPath -Arguments $appArgs -WorkingDirectory $projectRoot -IconLocation $iconPath -Description "FeintSignal Intelligence Dashboard control panel"
New-Shortcut -ShortcutPath (Join-Path $startMenuDir "FeintSignal.lnk") -TargetPath $powershellPath -Arguments $appArgs -WorkingDirectory $projectRoot -IconLocation $iconPath -Description "FeintSignal Intelligence Dashboard control panel"

# Dashboard: open straight into the Brave fullscreen app window (starts the stack silently).
$termArgs = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$projectRoot\launcher\fs-terminal.ps1`""
New-Shortcut -ShortcutPath (Join-Path $desktopPath "FeintSignal Dashboard.lnk") -TargetPath $powershellPath -Arguments $termArgs -WorkingDirectory $projectRoot -IconLocation $iconPath -Description "Open the FeintSignal dashboard in Brave fullscreen"
New-Shortcut -ShortcutPath (Join-Path $startMenuDir "FeintSignal Dashboard.lnk") -TargetPath $powershellPath -Arguments $termArgs -WorkingDirectory $projectRoot -IconLocation $iconPath -Description "Open the FeintSignal dashboard in Brave fullscreen"

Write-Host "Shortcuts installed: 'FeintSignal' (control panel) and 'FeintSignal Dashboard' (Brave fullscreen app window) on your Desktop and Start Menu."
