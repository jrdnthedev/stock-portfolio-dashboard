# Development Startup Guide

## Quick Start

### Option 1: Using npm (Recommended)
```bash
npm start
```
This will:
- Start Docker services (Postgres, Redis, Kafka)
- Wait for services to be healthy
- Activate Python virtual environment
- Start the FastAPI backend

### Option 2: Start Backend Only (with auto-check)
```bash
npm run start:backend
```
This will:
- Check if Kafka is running
- Auto-start Docker services if needed
- Start the backend

### Option 3: Direct PowerShell Scripts
```powershell
# Full startup
.\start-dev.ps1

# Backend only with auto-check
.\start-backend.ps1

# Stop all services
.\stop-dev.ps1
```

### Option 4: Manual Docker + Backend
```bash
# Start infrastructure
npm run docker:up

# Then in backend directory
cd backend
python main.py
```

## Stopping Services

```bash
# Stop all Docker services
npm stop

# Or manually
npm run docker:down
```

## Services and Ports

- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Kafka**: `localhost:9093` (external), `localhost:9092` (internal)
- **Zookeeper**: `localhost:2181`
- **Backend API**: `localhost:8000`

## Troubleshooting

### Kafka Connection Issues
If you get `NoBrokersAvailable` error:
1. Ensure Docker Desktop is running
2. Wait 30-60 seconds for Kafka to fully initialize
3. Run `npm start` which includes proper wait logic

### Services Not Starting
```bash
# Check Docker status
docker ps

# View service logs
docker-compose logs kafka
docker-compose logs postgres
docker-compose logs redis

# Restart all services
docker-compose down
docker-compose up -d
```

### Port Already in Use
```bash
# Find what's using the port (example: 8000)
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <process_id> /F
```

## First Time Setup

1. **Install Docker Desktop** (if not already installed)

2. **Create Python virtual environment** (if not already created):
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install Python dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Create .env file** in `backend/` directory with required variables

5. **Run the startup script**:
   ```bash
   npm start
   ```

## Development Workflow

Recommended workflow for daily development:

```bash
# Morning - Start everything
npm start

# During development - Backend will auto-reload on changes
# (no need to restart)

# End of day - Stop services
npm stop
```

## Alternative: Running Without Kafka

If you want to run the backend without Kafka for testing, you'll need to modify the lifespan function in `backend/main.py` to handle optional Kafka initialization.
