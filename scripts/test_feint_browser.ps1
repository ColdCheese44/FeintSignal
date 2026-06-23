# Tests the shared browser launcher without opening a browser.
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $projectRoot "launcher\feint-browser.ps1")

function Assert-True {
  param([bool]$Condition, [string]$Message)
  if (-not $Condition) { throw $Message }
}

function Assert-Equal {
  param($Expected, $Actual, [string]$Message)
  if ($Expected -ne $Actual) {
    throw "$Message Expected '$Expected', got '$Actual'."
  }
}

function Assert-Contains {
  param([array]$Values, [string]$Expected, [string]$Message)
  if ($Values -notcontains $Expected) { throw $Message }
}

function Assert-NotContains {
  param([array]$Values, [string]$Unexpected, [string]$Message)
  if ($Values -contains $Unexpected) { throw $Message }
}

$url = "http://127.0.0.1:5173"
$fakeBrave = "C:\Fake\Brave\brave.exe"

$plan = New-FeintBrowserLaunchPlan -Url $url -BrowserPath $fakeBrave
Assert-True $plan.UsePreferredBrowser "Expected explicit browser path to be used."
Assert-Equal "fullscreen" $plan.Mode "Default mode should be fullscreen."
Assert-Equal $fakeBrave $plan.FilePath "Unexpected browser path."
Assert-Contains $plan.ArgumentList "--new-window" "Expected new-window argument."
Assert-Contains $plan.ArgumentList "--start-fullscreen" "Expected fullscreen argument."
Assert-Contains $plan.ArgumentList $url "Expected URL argument."

$profileDir = "C:\Temp\FeintSignalTerminal"
$appPlan = New-FeintBrowserLaunchPlan -Url $url -Mode "maximized" -AppMode -ProfileDir $profileDir -BrowserPath $fakeBrave
Assert-Equal "maximized" $appPlan.Mode "Mode should resolve to maximized."
Assert-True $appPlan.AppMode "Expected app mode to be true."
Assert-Contains $appPlan.ArgumentList "--start-maximized" "Expected maximized argument."
Assert-Contains $appPlan.ArgumentList "--user-data-dir=$profileDir" "Expected dedicated user-data-dir argument."
Assert-Contains $appPlan.ArgumentList "--app=$url" "Expected app URL argument."
Assert-NotContains $appPlan.ArgumentList "--start-fullscreen" "Maximized mode should not add fullscreen."

$kioskPlan = New-FeintBrowserLaunchPlan -Url $url -Mode "kiosk" -BrowserPath $fakeBrave
Assert-Contains $kioskPlan.ArgumentList "--kiosk" "Kiosk should only be added when explicitly requested."

$normalPlan = New-FeintBrowserLaunchPlan -Url $url -Mode "normal" -BrowserPath $fakeBrave
Assert-Equal "normal" $normalPlan.Mode "Mode should resolve to normal."
Assert-NotContains $normalPlan.ArgumentList "--start-fullscreen" "Normal mode should not add fullscreen."
Assert-NotContains $normalPlan.ArgumentList "--start-maximized" "Normal mode should not add maximized."
Assert-NotContains $normalPlan.ArgumentList "--kiosk" "Normal mode should not add kiosk."

$invalidPlan = New-FeintBrowserLaunchPlan -Url $url -Mode "not-a-mode" -BrowserPath $fakeBrave
Assert-Equal "fullscreen" $invalidPlan.Mode "Invalid mode should fall back to fullscreen."
Assert-Contains $invalidPlan.ArgumentList "--start-fullscreen" "Invalid mode should use fullscreen argument."

$fallbackPlan = New-FeintBrowserLaunchPlan -Url $url -BrowserPath ""
Assert-True (-not $fallbackPlan.UsePreferredBrowser) "Empty browser path should produce fallback plan."
Assert-Contains $fallbackPlan.ArgumentList "--start-fullscreen" "Fallback plan should still expose the resolved default mode."

$oldMode = $env:FEINT_BROWSER_MODE
try {
  $env:FEINT_BROWSER_MODE = "maximized"
  Assert-Equal "maximized" (Get-FeintBrowserMode) "Environment mode should be honored."
} finally {
  $env:FEINT_BROWSER_MODE = $oldMode
}

Write-Host "Feint browser helper tests passed."
