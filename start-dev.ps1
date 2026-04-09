# start-dev.ps1 - Start all development services

$ErrorActionPreference = "Stop"

Write-Host "[START] Stock Portfolio Dashboard - Development Environment" -ForegroundColor Cyan
Write-Host ""

# Change to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Check Docker is running
Write-Host "[CHECK] Checking Docker..." -ForegroundColor Yellow
if (-not (Test-DockerRunning)) {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker is running" -ForegroundColor Green

# Clean up any existing services first to avoid stale state
Write-Host ""
Write-Host "[DOCKER] Cleaning up any existing services..." -ForegroundColor Yellow
$ErrorActionPreference = "SilentlyContinue"
docker-compose down *> $null
$ErrorActionPreference = "Stop"

# Start Docker Compose services
Write-Host "[DOCKER] Starting infrastructure services (Postgres, Redis, Kafka)..." -ForegroundColor Yellow
docker-compose up -d postgres redis zookeeper kafka

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start Docker services" -ForegroundColor Red
    exit 1
}

# Wait for services to be healthy
Write-Host ""
Write-Host "[WAIT] Waiting for services to be healthy..." -ForegroundColor Yellow

$maxWaitSeconds = 60
$waitedSeconds = 0
$servicesHealthy = $false

while ($waitedSeconds -lt $maxWaitSeconds) {
    Start-Sleep -Seconds 2
    $waitedSeconds += 2

    # Check service health
    $unhealthyServices = docker-compose ps --format json | ConvertFrom-Json | Where-Object {
        $_.Service -in @('postgres', 'redis', 'kafka') -and $_.Health -ne 'healthy'
    }

    if ($null -eq $unhealthyServices -or $unhealthyServices.Count -eq 0) {
        $servicesHealthy = $true
        break
    }

    $progressMsg = "  Waiting... ($waitedSeconds/$maxWaitSeconds seconds)"
    Write-Host $progressMsg -ForegroundColor Gray
}

if (-not $servicesHealthy) {
    Write-Host "[WARN] Services may not be fully healthy yet, but continuing..." -ForegroundColor Yellow
}
else {
    Write-Host "[OK] All services are healthy" -ForegroundColor Green
}

# Additional wait for Kafka to fully initialize
Write-Host "[WAIT] Giving Kafka additional time to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verify Kafka is actually running
$kafkaStatus = docker ps --filter "name=kafka" --filter "status=running" --format "{{.Names}}"
if (-not $kafkaStatus) {
    Write-Host "[ERROR] Kafka failed to start. Checking logs..." -ForegroundColor Red
    docker logs portfolio-kafka --tail 20
    Write-Host ""
    Write-Host "[ERROR] Please check the logs above. You may need to run 'docker-compose down' manually." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Kafka is running" -ForegroundColor Green

# Activate Python virtual environment
Write-Host ""
Write-Host "[PYTHON] Activating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
}
else {
    Write-Host "[WARN] Virtual environment not found at .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "   Continuing without activation..." -ForegroundColor Yellow
}

# Start Backend
Write-Host ""
Write-Host "[START] Starting FastAPI backend..." -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

Set-Location backend
python main.py
