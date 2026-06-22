# Run the FeintSignal backend (FastAPI + Uvicorn).
# Usage:  .\scripts\run_backend.ps1
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$venvActivate = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
} else {
    Write-Host "No .venv found. Create it with:  py -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt" -ForegroundColor Yellow
}

$backendHost = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { "127.0.0.1" }
$backendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8765" }

Write-Host "Starting FeintSignal backend on http://$backendHost`:$backendPort" -ForegroundColor Cyan
python -m uvicorn backend.main:app --host $backendHost --port $backendPort --reload
