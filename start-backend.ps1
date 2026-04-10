# start-backend.ps1 - Quick backend startup with service check

$ErrorActionPreference = "Stop"

Write-Host "[START] Starting Backend Server" -ForegroundColor Cyan

# Change to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Function to check if a service is reachable
function Test-ServiceReachable {
    param([string]$Host, [int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient($Host, $Port)
        $connection.Close()
        return $true
    }
    catch {
        return $false
    }
}

# Check if Kafka is running
Write-Host "[CHECK] Checking Kafka availability..." -ForegroundColor Yellow
if (-not (Test-ServiceReachable -Host "localhost" -Port 9093)) {
    Write-Host "[WARN] Kafka not detected on localhost:9093" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[INFO] Cleaning up any stale services..." -ForegroundColor Yellow
    $ErrorActionPreference = "SilentlyContinue"
    docker-compose down *> $null
    $ErrorActionPreference = "Stop"

    Write-Host "[INFO] Starting infrastructure services..." -ForegroundColor Yellow
    docker-compose up -d postgres redis zookeeper kafka

    Write-Host "[WAIT] Waiting for Kafka to be ready (this may take 30-60 seconds)..." -ForegroundColor Yellow
    $maxAttempts = 40
    $attempt = 0

    while ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 2
        if (Test-ServiceReachable -Host "localhost" -Port 9093) {
            Write-Host "[OK] Kafka port is open" -ForegroundColor Green
            Write-Host "[WAIT] Allowing Kafka additional time to initialize..." -ForegroundColor Yellow
            Start-Sleep -Seconds 15  # Longer buffer for Kafka to fully initialize
            Write-Host "[OK] Kafka should be ready" -ForegroundColor Green
            break
        }
        $attempt++
        Write-Host "  Attempt $attempt/$maxAttempts..." -ForegroundColor Gray
    }

    if ($attempt -eq $maxAttempts) {
        Write-Host "[ERROR] Kafka did not become ready in time" -ForegroundColor Red
        Write-Host "[ERROR] Checking Kafka logs..." -ForegroundColor Red
        docker logs portfolio-kafka --tail 20
        exit 1
    }
}
else {
    Write-Host "[OK] Kafka is already running" -ForegroundColor Green
}

# Activate virtual environment if exists
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

# Start backend
Write-Host ""
Write-Host "[START] Starting FastAPI backend..." -ForegroundColor Yellow
Write-Host ""
Set-Location backend
python main.py
