# Launch the full FeintSignal local stack: seed data, start backend, start frontend.
# Usage:  .\scripts\run_local.ps1
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# Activate venv if present.
$venvActivate = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) { . $venvActivate }

Write-Host "Seeding mock data..." -ForegroundColor Cyan
python scripts\seed_mock_data.py

Write-Host "Launching backend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-File", (Join-Path $PSScriptRoot "run_backend.ps1")

Write-Host "Launching frontend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-File", (Join-Path $PSScriptRoot "run_frontend.ps1")

Write-Host "FeintSignal local stack starting. Backend: http://127.0.0.1:8765  Frontend: http://127.0.0.1:5173" -ForegroundColor Green
