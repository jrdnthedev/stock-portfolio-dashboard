# Docker Setup Guide

## Prerequisites
- Docker Desktop installed and running
- Docker Compose v2.0+

## Getting Started

### 1. Environment Setup
Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

Edit `.env` with your actual API keys and configuration values.

### 2. Build and Start All Services
```bash
docker-compose up --build
```

Or run in detached mode:
```bash
docker-compose up -d --build
```

### 3. Access the Application
- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Kafka**: localhost:9093 (external), kafka:9092 (internal)

## Individual Service Commands

### Start specific services
```bash
docker-compose up backend postgres redis
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Stop services
```bash
docker-compose down
```

### Stop and remove volumes (clean slate)
```bash
docker-compose down -v
```

### Rebuild a specific service
```bash
docker-compose build backend
docker-compose up -d backend
```

## Development Workflow

### Backend Development
The backend service uses volume mounting for hot reload:
- Changes to `./backend` are reflected immediately
- Uvicorn runs with `--reload` flag in dev mode

### Frontend Development
For active development, you may prefer running Angular locally:
```bash
cd portfolio-dashboard
npm install
npm start
```

Then only run backend services:
```bash
docker-compose up postgres redis kafka zookeeper backend
```

## Service Health Checks

Check if all services are healthy:
```bash
docker-compose ps
```

## Troubleshooting

### Kafka connection issues
Kafka takes longer to start. If services fail, wait 30 seconds and restart:
```bash
docker-compose restart backend
```

### Port conflicts
If ports are already in use, modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Clear all data and restart
```bash
docker-compose down -v
docker-compose up --build
```

## Production Deployment

For production, update `docker-compose.yml`:
1. Remove volume mounts for backend
2. Set `DEBUG: "false"`
3. Use proper secrets management
4. Configure nginx for frontend with proper domain
5. Set up proper networking and security groups

## Database Migrations

To run database migrations:
```bash
docker-compose exec backend python -m alembic upgrade head
```

## Kafka Topics

Create Kafka topics:
```bash
docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic stock-updates \
  --partitions 3 \
  --replication-factor 1
```

List topics:
```bash
docker-compose exec kafka kafka-topics --list \
  --bootstrap-server localhost:9092
```
