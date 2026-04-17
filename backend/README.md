# Stock Portfolio Dashboard - Backend API

> FastAPI backend providing real-time market data, portfolio management, and performance analytics with event-driven architecture.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-464%20passed-brightgreen.svg)](backend/tests/)
[![Type Checked](https://img.shields.io/badge/type--checked-mypy-blue.svg)](http://mypy-lang.org/)

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)

---

## Features

### Core Capabilities
- ✅ **RESTful API** with standardized response envelopes
- ✅ **Real-time updates** via WebSocket with Redis-backed pub/sub
- ✅ **Event-driven architecture** using Kafka for price streaming and portfolio events
- ✅ **JWT authentication** with bcrypt password hashing and RBAC
- ✅ **API versioning** with header detection and backward compatibility
- ✅ **Comprehensive caching** using Redis with intelligent invalidation
- ✅ **Health monitoring** for PostgreSQL, Redis, and Kafka
- ✅ **Domain-Driven Design** with clean separation of concerns
- ✅ **Repository Pattern** for data access abstraction
- ✅ **Dependency Injection** with lightweight container

### Business Features
- 📊 Historical and real-time market data (OHLCV)
- 💼 Portfolio management with holdings tracking
- 📈 Real-time performance calculation and P&L analytics
- 🔔 Price movement alerts with configurable thresholds
- 🎯 Asset allocation and sector analysis
- 📸 Portfolio snapshots for historical tracking

---

## Technology Stack

| Category | Technologies |
|----------|-------------|
| **Framework** | FastAPI 0.115.0, Uvicorn 0.32.0 |
| **Database** | PostgreSQL, SQLAlchemy 2.0.36, psycopg 3.2.13 |
| **Caching** | Redis 5.0.1 |
| **Messaging** | Apache Kafka (kafka-python-ng 2.2.2) |
| **Authentication** | PyJWT 2.12.0, bcrypt 4.1.2 |
| **Validation** | Pydantic 2.9.2 |
| **Testing** | pytest 8.1.1, testcontainers 4.7.2 |
| **Type Checking** | mypy 1.9.0 (strict mode) |
| **Code Quality** | ruff 0.3.0, black 26.3.1 |

---

## Quick Start

---

## Quick Start

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 14+
- Redis 6+
- Apache Kafka 3+
- Docker (optional, for integration tests)

### Installation

1. **Activate virtual environment:**
   ```powershell
   # Windows PowerShell
   .\.venv\Scripts\activate

   # Linux/macOS
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Create `.env` file in the backend directory:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/stock_portfolio

   # Redis
   REDIS_HOST=localhost
   REDIS_PORT=6379

   # Kafka
   KAFKA_BOOTSTRAP_SERVERS=localhost:9093

   # JWT (CHANGE IN PRODUCTION!)
   JWT_SECRET_KEY=your-secret-key-min-32-chars-CHANGE-IN-PRODUCTION
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. **Seed the database:**
   ```bash
   python -m seed.run_seed
   ```

5. **Start the server:**
   ```bash
   python main.py
   ```

6. **Access the API:**
   - API: http://localhost:8000/api/v1
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/api/health

---

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Health & Status
```
GET  /                    # Root endpoint with API info
GET  /api/health          # Health check (PostgreSQL, Redis, Kafka)
```

#### Market Data (`/api/v1/market`)
```
GET  /market/prices/{ticker}              # Historical OHLCV data
GET  /market/prices/{ticker}/latest       # Latest price quote
GET  /market/fundamentals/{ticker}        # Company fundamentals
GET  /market/tickers                      # Available tickers list
```

#### Portfolio Management (`/api/v1/portfolio`)
```
GET    /portfolio/                        # List portfolios
GET    /portfolio/{id}                    # Portfolio details
GET    /portfolio/{id}/holdings           # Portfolio holdings
GET    /portfolio/{id}/performance        # Performance metrics
GET    /portfolio/{id}/allocation         # Asset allocation
POST   /portfolio/{id}/holdings           # Add holding
PUT    /portfolio/{id}/holdings/{hid}     # Update holding
DELETE /portfolio/{id}/holdings/{hid}     # Remove holding
```

#### WebSocket (`/ws`)
```
WS   /ws/portfolio?client_id={uuid}       # Real-time updates
GET  /ws/status                           # Connection stats
```

### Response Format

All endpoints return a standardized envelope:

```json
{
  "success": true,
  "data": { /* payload */ },
  "message": "Operation completed successfully",
  "errors": null,
  "metadata": {
    "correlation_id": "uuid-for-tracing",
    "count": 10
  },
  "timestamp": "2026-04-16T10:30:00.123456Z"
}
```

📖 **See**: [Response Formatter Documentation](docs/README.Formatter.md)

---

## Architecture
---

## Architecture

### Design Principles

The backend follows **Domain-Driven Design** (DDD) with:
- **Clean Architecture**: Clear separation between domain logic and infrastructure
- **Repository Pattern**: Abstracted data access layer
- **Dependency Injection**: Lightweight container for service management
- **Event-Driven**: Kafka-based event streaming for scalability

### Architectural Layers

```
┌─────────────────────────────────────────────┐
│         HTTP Routes Layer                   │
│  (routes_*.py - API endpoints)              │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│         Domain Services Layer               │
│  (business logic, domain models)            │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│    Infrastructure & Gateway Layer           │
│  (database, cache, Kafka, WebSocket)        │
└─────────────────────────────────────────────┘
```

### Project Structure

```
backend/
├── main.py                    # Application entry point
├── config.py                  # Configuration management
├── container.py               # Dependency injection container
├── routes_*.py                # HTTP API routes
│
├── api/                       # API layer
│   ├── dependencies.py        # FastAPI dependencies
│   └── versioning.py          # Version detection
│
├── domains/                   # Business logic (DDD)
│   ├── market_data/           # Market data domain
│   │   ├── models/            # Domain models
│   │   └── service/           # Business services
│   └── portfolio/             # Portfolio domain
│       ├── models/            # Portfolio entities
│       ├── repositories/      # Repository interfaces
│       └── services/          # Business services
│
├── infrastructure/            # Infrastructure implementations
│   └── repositories/          # SQLAlchemy repositories
│
├── gateway/                   # Infrastructure services
│   ├── cache.py               # Redis caching
│   ├── formatter.py           # Response formatting
│   ├── health.py              # Health checks
│   └── websocket_manager.py   # WebSocket connections
│
├── middleware/                # HTTP middleware
│   ├── auth.py                # JWT authentication
│   ├── logging.py             # Request logging
│   └── versioning.py          # API versioning
│
├── database/                  # Data persistence
│   ├── database.py            # SQLAlchemy setup
│   └── models.py              # ORM models
│
├── websocket_handler/         # WebSocket handlers
├── seed/                      # Database seeding
├── tests/                     # Test suite (464 tests)
└── docs/                      # Detailed documentation
```

### Key Components

#### Event-Driven Architecture

**Kafka Topics:**
- `market.prices.live` - Real-time price updates (5s interval)
- `portfolio.holdings.changed` - Portfolio modifications
- `portfolio.alerts` - Price movement alerts

**Background Services:**
- **PricePublisher**: Publishes mock price data every 5 seconds
- **PriceEventConsumer**: Consumes price updates for portfolio recalculation
- **AlertPublisher**: Monitors prices and publishes threshold alerts
- **PortfolioPerformanceOrchestrator**: Coordinates P&L updates and WebSocket broadcasts

#### Caching Strategy

**Redis Cache Keys:**
```
market:prices:{ticker}              # TTL: 30 min
market:fundamentals:{ticker}        # TTL: 30 min
portfolio:{id}                      # TTL: 30 min (invalidated on mutation)
portfolio:{id}:performance          # TTL: 30 min (invalidated on mutation)
```

**Cache Invalidation:**
- Automatic on POST/PUT/DELETE operations
- Pattern-based bulk deletion
- Get-or-set pattern for consistency

📖 **See**: [Caching Documentation](docs/README.Cache.md)

#### Authentication & Security

- **JWT tokens** with access (30 min) and refresh (7 days)
- **bcrypt password hashing** with automatic 72-byte truncation
- **Role-based access control** (RBAC)
- **Correlation IDs** for distributed tracing

📖 **See**: [Authentication Documentation](docs/README.Auth.md)

---

## Development

---

## Development

### Running the Application

Start the development server with auto-reload:
```bash
python main.py
```

Or use uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality Tools

**Type Checking:**
```bash
mypy .                    # Full type check
mypy routes_market.py     # Check specific file
```

**Linting:**
```bash
ruff check .              # Run linter
ruff check --fix .        # Auto-fix issues
```

**Formatting:**
```bash
black .                   # Format all files
```

**Security Scanning:**
```bash
bandit -r . -ll           # Security vulnerability scan
```

### Development Standards

- ✅ **Type hints** on all functions
- ✅ **Google-style docstrings** for public APIs
- ✅ **>80% test coverage** requirement
- ✅ **PEP 8** naming conventions
- ✅ **100 character** line length limit
- ✅ **Sorted imports** (ruff/isort)

---

## Testing

---

## Testing

### Test Suite

**Total: 464 tests** (461 passed, 3 skipped)
- **Unit Tests**: 419 tests (fast, mocked dependencies)
- **Integration Tests**: 45 tests (real PostgreSQL via testcontainers)

### Running Tests

**All tests:**
```bash
pytest
```

**Unit tests only:**
```bash
pytest tests/test_*.py -k "not integration"
```

**Integration tests (requires Docker):**
```bash
pytest tests/integration_test_*.py
```

**With coverage:**
```bash
pytest --cov=backend --cov-report=html --cov-report=term-missing
```

**Specific test file:**
```bash
pytest tests/test_portfolio_service.py -v
```

**Parallel execution (faster):**
```bash
pytest -n auto
```

**Pattern matching:**
```bash
pytest -k "websocket or price_event" -v
```

### Test Categories

**Unit Tests** (419 tests) - Fast, no external dependencies:
- Market data services and adapters
- Portfolio services (CRUD, performance, snapshots)
- Authentication and JWT handling
- Cache operations and invalidation
- Response formatting
- WebSocket manager
- Health checks

**Integration Tests** (45 tests) - Real database via testcontainers:
- Market data endpoints (23 tests)
- Portfolio management endpoints (22 tests)
- Full request/response cycle
- Database operations

📖 **See**: [Integration Testing Documentation](docs/README.Integration.md)

---

## Deployment

### Using Docker

Build the image:
```bash
docker build -t stock-portfolio-backend .
```

Run the container:
```bash
docker run -p 8000:8000 --env-file .env stock-portfolio-backend
```

### Using Docker Compose

Start the full stack (PostgreSQL, Redis, Kafka, Backend):
```bash
docker-compose up -d
```

### Production Checklist

- [ ] Generate strong `JWT_SECRET_KEY` (min 32 chars)
- [ ] Set `DEBUG=False`
- [ ] Configure CORS origins
- [ ] Enable database connection pooling
- [ ] Configure Redis persistence
- [ ] Set up Kafka replication
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Enable automated backups
- [ ] Set up alerting

### Environment Variables

```env
# Database

DATABASE_URL=postgresql://user:password@localhost:5432/stock_portfolio

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_DEFAULT_TTL=1800

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9093
KAFKA_TOPIC_PREFIX=stock-portfolio

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars-CHANGE-IN-PRODUCTION
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

---

## Documentation

Detailed documentation is available in the [`docs/`](docs/) directory:

### Infrastructure & Services
| Document | Description |
|----------|-------------|
| [Cache Service](docs/README.Cache.md) | Redis caching, TTL strategies, invalidation patterns |
| [Response Formatter](docs/README.Formatter.md) | Standardized envelopes, error formatting |
| [Health Monitoring](docs/README.Health.md) | PostgreSQL, Redis, Kafka health checks |
| [WebSocket Manager](docs/README.WebSocket.md) | Real-time connections, pub/sub, topics |

### Architecture & Design
| Document | Description |
|----------|-------------|
| [Domain Architecture](docs/README.Domains.md) | DDD principles, market data & portfolio domains |
| [API Versioning](docs/README.Versioning.md) | Versioning strategy, backward compatibility |
| [Authentication](docs/README.Auth.md) | JWT, password hashing, RBAC |

### Testing
| Document | Description |
|----------|-------------|
| [Integration Tests](docs/README.Integration.md) | Testcontainers, database fixtures, test setup |

---

## Contributing

### Development Workflow

1. Create a feature branch
2. Write tests for new functionality
3. Implement the feature
4. Run tests and type checking
5. Format and lint code
6. Update documentation
7. Submit pull request

### Code Standards

- **Type hints**: All functions must have type annotations
- **Docstrings**: Google-style docstrings for public APIs
- **Testing**: Maintain >80% code coverage
- **Naming**: PEP 8 conventions
- **Imports**: Sorted with ruff/isort
- **Line length**: 100 characters

---

## License

[Add license information]

---

## Support

For issues, questions, or contributions, please refer to the project repository.

**Version**: 1.0.0
**API Version**: v1
**Test Coverage**: 461/464 tests passing (99.4%)

