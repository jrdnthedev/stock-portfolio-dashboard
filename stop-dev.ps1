# stop-dev.ps1 - Stop all development services

Write-Host "[STOP] Stopping Stock Portfolio Dashboard services..." -ForegroundColor Yellow

# Change to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Stop Docker Compose services
Write-Host "[DOCKER] Stopping Docker services..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "[OK] All services stopped" -ForegroundColor Green
