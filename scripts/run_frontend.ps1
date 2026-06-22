# Run the FeintSignal frontend (Vite dev server).
# Usage:  .\scripts\run_frontend.ps1
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $repoRoot "frontend"
Set-Location $frontend

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    npm install
}

Write-Host "Starting FeintSignal frontend (Vite)..." -ForegroundColor Cyan
npm run dev
