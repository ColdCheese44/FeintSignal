<#
  Shared Feint browser launcher.

  Browser-opening paths should prefer Brave in fullscreen mode, while preserving a safe
  default-browser fallback when Brave is not available.
#>

function Get-FeintBrowserMode {
  param([string]$Mode)

  $candidate = if ($Mode) { $Mode } elseif ($env:FEINT_BROWSER_MODE) { $env:FEINT_BROWSER_MODE } else { "fullscreen" }

  switch ($candidate.ToLowerInvariant()) {
    "fullscreen" { return "fullscreen" }
    "maximized"  { return "maximized" }
    "normal"     { return "normal" }
    "kiosk"      { return "kiosk" }
    default      { return "fullscreen" }
  }
}

function Get-FeintBravePath {
  param([string]$BrowserPath)

  if ($BrowserPath -and (Test-Path -LiteralPath $BrowserPath)) {
    return $BrowserPath
  }

  if ($env:FEINT_BROWSER_PATH -and (Test-Path -LiteralPath $env:FEINT_BROWSER_PATH)) {
    return $env:FEINT_BROWSER_PATH
  }

  $preference = if ($env:FEINT_BROWSER) { $env:FEINT_BROWSER.Trim() } else { "brave" }
  if ($preference.ToLowerInvariant() -eq "default") {
    return $null
  }

  if ([System.IO.Path]::IsPathRooted($preference) -and (Test-Path -LiteralPath $preference)) {
    return $preference
  }

  if ($preference -and $preference.ToLowerInvariant() -notin @("brave", "brave.exe", "brave-browser")) {
    $preferredCommand = Get-Command $preference -ErrorAction SilentlyContinue
    if ($preferredCommand -and $preferredCommand.Source) {
      return $preferredCommand.Source
    }
  }

  $paths = @(
    "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe"
  )

  foreach ($path in $paths) {
    if ($path -and (Test-Path -LiteralPath $path)) {
      return $path
    }
  }

  foreach ($commandName in @("brave.exe", "brave", "brave-browser")) {
    $command = Get-Command $commandName -ErrorAction SilentlyContinue
    if ($command -and $command.Source) {
      return $command.Source
    }
  }

  return $null
}

function New-FeintBrowserLaunchPlan {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Url,

    [string]$Mode,

    [switch]$AppMode,

    [string]$ProfileDir,

    [string]$BrowserPath
  )

  $resolvedMode = Get-FeintBrowserMode -Mode $Mode
  $resolvedBrowser = if ($PSBoundParameters.ContainsKey("BrowserPath")) { $BrowserPath } else { Get-FeintBravePath }
  $args = @("--new-window")

  switch ($resolvedMode) {
    "fullscreen" { $args += "--start-fullscreen" }
    "maximized"  { $args += "--start-maximized" }
    "kiosk"      { $args += "--kiosk" }
    "normal"     { }
  }

  if ($ProfileDir) {
    $args += "--user-data-dir=$ProfileDir"
  }

  if ($AppMode) {
    $args += "--app=$Url"
  } else {
    $args += $Url
  }

  return [pscustomobject]@{
    Url = $Url
    Mode = $resolvedMode
    UsePreferredBrowser = [bool]$resolvedBrowser
    FilePath = $resolvedBrowser
    ArgumentList = $args
    AppMode = [bool]$AppMode
  }
}

function Open-FeintBrowser {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory = $true)]
    [string]$Url,

    [string]$Mode,

    [switch]$AppMode,

    [string]$ProfileDir,

    [string]$BrowserPath
  )

  $planArgs = @{
    Url = $Url
    Mode = $Mode
    AppMode = $AppMode
    ProfileDir = $ProfileDir
  }
  if ($PSBoundParameters.ContainsKey("BrowserPath")) {
    $planArgs.BrowserPath = $BrowserPath
  }

  $plan = New-FeintBrowserLaunchPlan @planArgs

  try {
    if ($plan.UsePreferredBrowser) {
      Start-Process -FilePath $plan.FilePath -ArgumentList $plan.ArgumentList | Out-Null
      return $true
    }

    Write-Warning "Brave was not found. Falling back to the default browser for $Url."
    Start-Process $Url | Out-Null
    return $true
  } catch {
    Write-Warning "Unable to open $Url in a browser: $($_.Exception.Message)"
    return $false
  }
}
