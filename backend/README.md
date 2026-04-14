# Stock Portfolio Dashboard - Backend API

FastAPI backend for the Stock Portfolio Dashboard application providing real-time market data, portfolio management, and performance analytics with event-driven architecture.

## Architecture Overview

The backend follows a **Domain-Driven Design** (DDD) approach with **Repository Pattern**, **Dependency Injection**, and **Event-Driven Architecture** for scalability and maintainability:

```
backend/
├── main.py                 # FastAPI application entry point with lifespan handlers
├── config.py               # Application configuration (Pydantic Settings)
├── container.py            # Dependency injection container (pure Python)
├── routes_market.py        # Market data API routes (/api/v1/market)
├── routes_portfolio.py     # Portfolio management API routes (/api/v1/portfolio)
├── routes_websocket.py     # WebSocket routes for real-time updates (/ws)
│
├── api/                    # API layer
│   ├── dependencies.py     # FastAPI dependency injection helpers
│   └── versioning.py       # API versioning strategy and router creation
│
├── database/               # Database layer
│   ├── database.py         # SQLAlchemy engine and session management
│   └── models.py           # Database models (SQLAlchemy ORM)
│
├── domains/                # Domain business logic (DDD)
│   ├── market_data/        # Market data domain
│   │   ├── models/         # Domain models (PricePoint, Ticker, Fundamental)
│   │   │   └── models.py
│   │   └── service/        # Market data services
│   │       ├── market_data_service.py    # Core market data orchestration
│   │       ├── pricing_adapter.py        # Mock price generation & Kafka publishing
│   │       ├── fundamentals_adapter.py   # Fundamentals data integration
│   │       └── price_publisher.py        # Background price publisher (5s interval)
│   └── portfolio/          # Portfolio management domain
│       ├── models/         # Portfolio domain models (Portfolio, Holding, AlertConfig)
│       │   └── models.py
│       ├── repositories/   # Repository interfaces (Repository Pattern)
│       │   └── portfolio_repository.py
│       └── services/       # Portfolio services
│           ├── portfolio_service.py      # Portfolio CRUD with Kafka event publishing
│           ├── performance_calculator.py # Real-time P&L calculation
│           ├── snapshot_service.py       # Portfolio snapshot management
│           ├── alert_publisher.py        # Price movement alert detection & publishing
│           └── price_event_consumer.py   # Kafka consumer & orchestrator
│
├── infrastructure/         # Infrastructure implementations
│   └── repositories/       # Repository implementations
│       └── sqlalchemy_portfolio_repository.py  # SQLAlchemy repository adapters
│
├── gateway/                # Gateway/infrastructure layer
│   ├── cache.py            # Redis caching service with key generation utilities
│   ├── formatter.py        # Response envelope formatting (Pydantic models)
│   ├── health.py           # Health check monitoring (PostgreSQL, Redis, Kafka)
│   └── websocket_manager.py # Redis-backed WebSocket manager with pub/sub
│
├── middleware/             # HTTP middleware
│   ├── auth.py             # JWT authentication (bcrypt password hashing, token management)
│   ├── logging.py          # Request logging with UUID correlation IDs
│   └── versioning.py       # API version detection and routing
│
├── websocket_handler/      # WebSocket handlers
│   ├── handler.py          # WebSocket message handlers
│   └── connection_store.py # Active connection management
│
├── seed/                   # Database seeding
│   ├── seed_data.py        # In-memory seed data management
│   ├── seed_database.py    # Database seeding with realistic market data
│   └── run_seed.py         # Seed script with service integration
│
├── tests/                  # Unit and integration tests (464 tests, 461 passed)
│   ├── conftest.py         # Pytest configuration with testcontainers
│   ├── test_fixtures.py    # Shared test fixtures and mock helpers
│   ├── test_*.py           # Unit tests (419 tests)
│   └── integration_test_*.py # Integration tests with PostgreSQL (45 tests)
│
└── docs/                   # Detailed documentation
    ├── README.Auth.md         # JWT authentication & password hashing
    ├── README.Cache.md        # Redis caching strategies & invalidation
    ├── README.Formatter.md    # Response envelope patterns
    ├── README.Health.md       # Health check implementation
    ├── README.WebSocket.md    # WebSocket real-time updates
    ├── README.Domains.md      # Domain-driven design guide
    ├── README.Versioning.md   # API versioning strategy
    └── README.Integration.md  # Integration testing with testcontainers
```

## Key Features

### Core Functionality
- **RESTful API** with standardized response envelopes (success, data, message, errors, metadata, timestamp)
- **API Versioning** with header-based version detection (`API-Version: v1`) and backward compatibility
- **Real-time updates** via WebSocket with Redis-backed connection registry and topic subscriptions
- **Event-driven architecture** with Kafka for:
  - Price streaming (`market.prices.live`)
  - Portfolio change events (`portfolio.holdings.changed`)
  - Price movement alerts (`portfolio.alerts`)
- **Domain-driven design** with clear separation between business logic and infrastructure
- **Repository Pattern** for data access abstraction and testability
- **Dependency Injection** with lightweight pure-Python DI container

### Authentication & Security
- **JWT-based authentication** with access and refresh tokens
- **bcrypt password hashing** with automatic truncation (72-byte limit)
- **Role-based access control** (RBAC) with `require_role()` and `require_any_role()` dependencies
- **Token validation** with type checking (prevents refresh token misuse)
- **Request correlation IDs** (UUID) for distributed tracing

### Background Services (Lifespan Handlers)
- **PricePublisher**: Publishes mock OHLCV price events every 5 seconds to Kafka
- **PriceEventConsumer**: Consumes price events from Kafka for portfolio updates
- **AlertPublisher**: Monitors price movements and publishes alerts when thresholds are exceeded
- **PortfolioPerformanceOrchestrator**: Coordinates:
  - Real-time price updates
  - Portfolio P&L recalculation
  - Alert detection and publishing
  - WebSocket broadcasts to connected clients

### Infrastructure
- **Health monitoring** for PostgreSQL, Redis, and Kafka with detailed status reporting
- **Request tracing** with UUID-based correlation IDs in all requests and responses
- **Caching layer** using Redis with:
  - Intelligent TTL strategies (30 min default)
  - Cache key generation utilities
  - Automatic invalidation on portfolio changes
  - Pipeline support for bulk operations
- **WebSocket manager** with:
  - Topic-based subscriptions for selective updates
  - Redis-backed connection registry for horizontal scaling
  - Client tracking and status monitoring
- **Request logging** middleware with correlation IDs, method, path, and timing metrics

## Technology Stack

- **Framework**: FastAPI 0.115.0
- **Database**: PostgreSQL with SQLAlchemy 2.0.36
- **Database Driver**: psycopg 3.2.13
- **Cache**: Redis 5.0.1
- **Message Broker**: Kafka (kafka-python-ng 2.2.2)
- **Validation**: Pydantic 2.9.2 with pydantic-settings 2.6.0
- **Authentication**: PyJWT 2.12.0 with bcrypt 4.1.2
- **Type Checking**: mypy 1.9.0 (strict mode, disallow_untyped_defs)
- **Linting**: ruff 0.3.0, black 26.3.1
- **Testing**: pytest 8.1.1 with pytest-cov 4.1.0, pytest-asyncio 0.23.6
- **Integration Testing**: testcontainers 4.7.2 with PostgreSQL containers
- **ASGI Server**: uvicorn 0.32.0
- **HTTP Client**: httpx 0.27.2

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Apache Kafka 3+

### Installation

1. **Activate the virtual environment:**
   ```powershell
   .\.venv\Scripts\activate  # Windows PowerShell
   ```
   ```bash
   source .venv/bin/activate  # Linux/macOS
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the `backend/` directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/stock_portfolio
   JWT_SECRET_KEY=your-secret-key-min-32-chars-CHANGE-IN-PRODUCTION
   REDIS_HOST=localhost
   REDIS_PORT=6379
   KAFKA_BOOTSTRAP_SERVERS=localhost:9093
   ```

4. **Initialize the database:**
   ```bash
   # Run migrations (if using Alembic)
   alembic upgrade head

   # Or seed the database with sample data
   python -m seed.run_seed
   ```

5. **Run the development server:**
   ```bash
   python main.py
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API:**
   - API Base: `http://localhost:8000/api/v1`
   - Interactive Docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - Health Check: `http://localhost:8000/api/health`

## API Endpoints

### Health & Documentation
- `GET /` - Root endpoint with API status and version information
- `GET /api/health` - Comprehensive health check
  - Checks: PostgreSQL, Redis, Kafka connectivity
  - Returns: 200 (healthy) or 503 (unhealthy)
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Market Data (`/api/v1/market`)
- `GET /api/v1/market/prices/{ticker}` - Historical OHLCV price data
  - Query params: `from=YYYY-MM-DD`, `to=YYYY-MM-DD` (optional date filtering)
  - Returns: Array of PricePoint objects with date, open, high, low, close, volume
  - Caching: 30-minute TTL per ticker
  - Example: `/api/v1/market/prices/AAPL?from=2024-01-01&to=2024-01-31`

- `GET /api/v1/market/prices/{ticker}/latest` - Latest price quote
  - Returns: Current price, change, change_percent, volume, timestamp
  - Caching: 30-minute TTL
  - Example: `/api/v1/market/prices/AAPL/latest`

- `GET /api/v1/market/fundamentals/{ticker}` - Company fundamentals
  - Returns: Company name, sector, industry, market_cap, pe_ratio, eps, revenue
  - Caching: 30-minute TTL
  - Example: `/api/v1/market/fundamentals/AAPL`

- `GET /api/v1/market/tickers` - List available tickers
  - Query params: `sector`, `exchange`, `asset_class` (optional filters)
  - Returns: Array of ticker objects with symbol, name, sector, exchange info
  - Supports case-insensitive filtering
  - Caching: 30-minute TTL per filter combination
  - Example: `/api/v1/market/tickers?sector=Technology&exchange=NASDAQ`

### Portfolio Management (`/api/v1/portfolio`)

**Portfolio Operations:**
- `GET /api/v1/portfolio/` - List all portfolios
  - Query params: `owner` (optional filter by owner)
  - Returns: Array of portfolio summaries

- `GET /api/v1/portfolio/{id}` - Get portfolio details
  - Returns: Portfolio with name, owner, currency, created/updated timestamps
  - Caching: 30-minute TTL

- `GET /api/v1/portfolio/{id}/holdings` - Get all portfolio holdings
  - Returns: Array of holdings with ticker, quantity, avg_cost_basis, current P&L
  - Includes ticker name resolution
  - Caching: 30-minute TTL

- `GET /api/v1/portfolio/{id}/performance` - Get portfolio performance metrics
  - Query params: `from=YYYY-MM-DD`, `to=YYYY-MM-DD` (optional date filtering)
  - Returns:
    - Total value, cost basis, unrealized P&L
    - Return percentage, gain/loss amounts
    - Sector allocation with weights
    - Individual holdings performance
  - Caching: 30-minute TTL

- `GET /api/v1/portfolio/{id}/allocation` - Get asset allocation breakdown
  - Returns: Allocation by sector with weights, values, and counts
  - Caching: 30-minute TTL

**Holdings Operations (Triggers Cache Invalidation & Kafka Events):**
- `POST /api/v1/portfolio/{id}/holdings` - Add new holding
  - Body: `{ticker_id: uuid, quantity: float, avg_cost_basis: float}`
  - Publishes: `portfolio.holdings.changed` event to Kafka
  - Invalidates: Portfolio, holdings, performance, allocation caches
  - Returns: Created holding object

- `PUT /api/v1/portfolio/{id}/holdings/{hid}` - Update existing holding
  - Body: `{quantity?: float, avg_cost_basis?: float}` (supports partial updates)
  - Publishes: `portfolio.holdings.changed` event to Kafka
  - Invalidates: Portfolio, holdings, performance, allocation caches
  - Returns: Updated holding object

- `DELETE /api/v1/portfolio/{id}/holdings/{hid}` - Delete holding
  - Publishes: `portfolio.holdings.changed` event to Kafka
  - Invalidates: Portfolio, holdings, performance, allocation caches
  - Returns: 204 No Content

### WebSocket (`/ws`)
- `WS /ws/portfolio?client_id={uuid}` - Real-time portfolio updates
  - **Client → Server Messages:**
    - `{"action": "subscribe", "topic": "portfolio:{id}"}` - Subscribe to portfolio updates
    - `{"action": "unsubscribe", "topic": "portfolio:{id}"}` - Unsubscribe from updates
    - `{"action": "ping"}` - Keep-alive ping
  - **Server → Client Messages:**
    - `{"event": "portfolio.performance", "data": {...}}` - Performance update
    - `{"event": "subscribed", "topic": "portfolio:{id}"}` - Subscription confirmation
    - `{"event": "unsubscribed", "topic": "portfolio:{id}"}` - Unsubscription confirmation
    - `{"event": "pong"}` - Ping response
  - Connection tracked in Redis with topic subscriptions

- `GET /ws/status` - WebSocket connection statistics
  - Returns: Active connection count, list of connected client IDs
  - For monitoring and debugging

### API Versioning

The API supports versioning through the `API-Version` header:

```http
GET /api/v1/market/prices/AAPL
API-Version: v1
```

- Default version: `v1`
- Version detection: Header-based with fallback to URL path
- Backward compatibility: Maintained across versions
- See [docs/README.Versioning.md](docs/README.Versioning.md) for details

### Response Format

All HTTP endpoints return a standardized envelope format:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully",
  "errors": null,
  "metadata": {
    "filters": {...},
    "count": 10,
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "timestamp": "2026-04-13T10:30:00.123456Z"
}
```

**Envelope Fields:**
- `success`: Boolean indicating request success
- `data`: Response payload (null on error)
- `message`: Human-readable status message (null or descriptive)
- `errors`: Array of ErrorDetail objects (null on success)
  - Each error: `{code: str, message: str, field?: str, details?: object}`
- `metadata`: Additional context
  - Always includes: `correlation_id` (UUID for request tracing)
  - Optional: `filters`, `count`, `pagination`, custom fields
- `timestamp`: ISO 8601 timestamp with microseconds and UTC timezone

**Error Response Example:**
```json
{
  "success": false,
  "data": null,
  "message": "Validation failed",
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Quantity must be positive",
      "field": "quantity",
      "details": {"value": -10, "constraint": "positive"}
    }
  ],
  "metadata": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440001"
  },
  "timestamp": "2026-04-13T10:30:01.234567Z"
}
```

See [docs/README.Formatter.md](docs/README.Formatter.md) for complete specification.

## Development

### Running the Application

Start the development server with auto-reload:
```bash
python main.py
```

Or use uvicorn directly with custom settings:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
```

The API will be available at:
- API Base: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/api/health`

### Running Tests

The backend has comprehensive test coverage with **464 tests (461 passed, 3 skipped)**:

**Run all tests:**
```bash
python -m pytest tests/
```

**Run with coverage report:**
```bash
python -m pytest tests/ --cov=. --cov-report=term-missing
```

**Run only unit tests:**
```bash
python -m pytest tests/ -k "not integration"
```

**Run only integration tests:**
```bash
python -m pytest tests/integration_test_*.py
```

**Run specific test file:**
```bash
python -m pytest tests/test_portfolio_service.py -v
```

**Run tests in parallel (faster):**
```bash
python -m pytest tests/ -n auto
```

### Test Structure

- **Unit Tests** (419 tests): Fast, isolated tests with mocked dependencies
  - Market data services
  - Portfolio services
  - Cache operations
  - Authentication & JWT
  - Response formatting
  - WebSocket manager
  - Performance calculations

- **Integration Tests** (45 tests): End-to-end tests with real PostgreSQL using testcontainers
  - Market data endpoints
  - Portfolio management endpoints
  - Database operations
  - Full request/response cycle

### Code Quality

**Type Checking:**
```bash
mypy .
```

**Linting:**
```bash
ruff check .
```

**Auto-fix linting issues:**
```bash
ruff check --fix .
```

**Code Formatting:**
```bash
black .
```

**Security Scanning:**
```bash
bandit -r . -ll
```

## Documentation

Detailed documentation is available in the `docs/` folder:

### Infrastructure & Gateway
- **[Cache Service](docs/README.Cache.md)** - Redis caching implementation, TTL strategies, cache invalidation patterns
- **[Response Formatter](docs/README.Formatter.md)** - Standardized response envelopes, error formatting, Pydantic models
- **[Health Monitoring](docs/README.Health.md)** - PostgreSQL, Redis, and Kafka health checks with status reporting
- **[WebSocket Manager](docs/README.WebSocket.md)** - Real-time communication, connection management, topic subscriptions, Redis pub/sub

### Domain Layer
- **[Domains Architecture](docs/README.Domains.md)** - Complete guide to market data and portfolio domains
  - Market Data Services (pricing, fundamentals, publishing)
  - Portfolio Services (CRUD, performance calculation, snapshots, alerts)
  - Event-driven architecture with Kafka
  - Caching strategies and error handling

### Authentication & Security
- **[Authentication](docs/README.Auth.md)** - JWT authentication, password hashing with bcrypt, RBAC, token management

### API Design
- **[API Versioning](docs/README.Versioning.md)** - Versioning strategy, header-based detection, backward compatibility

### Testing
- **[Integration Testing](docs/README.Integration.md)** - Integration testing with testcontainers, database fixtures, test organization

## Project Structure Details

### Dependency Injection Container

The application uses a lightweight pure-Python DI container (`container.py`) for:
- **Singleton services**: Database engine, session factory, application settings
- **Factory methods**: Database sessions, repositories, services
- **Lifecycle management**: Proper resource cleanup and connection pooling
- **Testing support**: Easy mocking and dependency replacement

Example usage:
```python
from backend.container import Container

container = Container()
with container.get_db_session() as session:
    portfolio_service = container.get_portfolio_service(session)
    portfolio = portfolio_service.create_portfolio("My Portfolio", "user123")
```

### Repository Pattern

The application implements the Repository Pattern for data access:

- **Interfaces**: Abstract repositories in `domains/portfolio/repositories/`
- **Implementations**: SQLAlchemy adapters in `infrastructure/repositories/`
- **Benefits**:
  - Decoupling business logic from data access
  - Easy testing with mock repositories
  - Flexibility to swap implementations
  - Clean separation of concerns

Example:
```python
# Domain interface
class PortfolioRepository(Protocol):
    def create(self, portfolio: Portfolio) -> Portfolio: ...
    def get_by_id(self, portfolio_id: UUID) -> Portfolio | None: ...

# Infrastructure implementation
class SQLAlchemyPortfolioRepository(PortfolioRepository):
    def __init__(self, session: Session):
        self.session = session
```

### Event-Driven Architecture

The application uses Kafka for event-driven communication:

**Topics:**
- `market.prices.live` - Real-time price updates (published every 5 seconds)
- `portfolio.holdings.changed` - Portfolio modification events
- `portfolio.alerts` - Price movement alerts

**Producers:**
- PricePublisher - Publishes mock OHLCV price data
- PortfolioService - Publishes holding change events
- AlertPublisher - Publishes price movement alerts

**Consumers:**
- PriceEventConsumer - Consumes price updates and triggers portfolio recalculation
- PortfolioPerformanceOrchestrator - Coordinates price updates with performance calculations and WebSocket broadcasts

### Caching Strategy

The application uses Redis for intelligent caching:

**Cache Keys:**
- `market:prices:AAPL` - Historical price data per ticker
- `market:fundamentals:AAPL` - Fundamental data per ticker
- `portfolio:123` - Portfolio details
- `portfolio:123:performance` - Portfolio performance metrics

**TTL Strategy:**
- Market data: 30 minutes (semi-static)
- Portfolio data: 30 minutes with invalidation on mutations
- WebSocket connections: Session-based TTL

**Invalidation:**
- Automatic on portfolio mutations (POST/PUT/DELETE holdings)
- Pattern-based deletion for bulk operations
- Cache-aside pattern for data consistency

See [docs/README.Cache.md](docs/README.Cache.md) for complete implementation details.

## Environment Variables

Required environment variables in `.env`:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/stock_portfolio

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_DEFAULT_TTL=1800

# Kafka Configuration
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

## Production Deployment

### Using Docker

Build the Docker image:
```bash
docker build -t stock-portfolio-backend .
```

Run the container:
```bash
docker run -p 8000:8000 --env-file .env stock-portfolio-backend
```

### Using Docker Compose

The project includes a `docker-compose.yml` for running the full stack:

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache
- Kafka message broker
- Backend API

### Production Checklist

- [ ] Change `JWT_SECRET_KEY` to a secure random value (min 32 characters)
- [ ] Set `DEBUG=False` in production
- [ ] Configure proper CORS origins
- [ ] Set up database connection pooling
- [ ] Configure Redis persistence
- [ ] Set up Kafka replication
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Enable database backups

## Contributing

### Development Workflow

1. Create a feature branch
2. Write tests for new functionality
3. Implement the feature
4. Run tests and type checking
5. Format code with black
6. Lint with ruff
7. Update documentation
8. Submit pull request

### Code Standards

- **Type hints**: All functions must have type annotations
- **Docstrings**: Use Google-style docstrings for public APIs
- **Testing**: Maintain >80% code coverage
- **Naming**: Follow PEP 8 conventions
- **Imports**: Sorted with isort/ruff
- **Line length**: 100 characters (configured in ruff/black)

## License

[Add license information]

## Support

For issues, questions, or contributions, please refer to the project repository.

**Test Suite**: 315 total tests (270 unit + 45 integration)

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/test_*.py

# Run integration tests only (requires Docker)
pytest tests/integration_test_*.py

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_market_routes.py -v

# Run tests matching pattern
pytest -k "websocket or price_event" -v

# Run with verbose output and show print statements
pytest -v -s
```

**Test Categories:**
- **Unit Tests**: Fast, no external dependencies (mocked DB, cache, Kafka)
- **Integration Tests**: Use testcontainers for PostgreSQL, test full API flows
- **Component Tests**: Test domain services, adapters, calculators

## Type Checking

```bash
# Run mypy type checking
mypy .

# Check specific file
mypy routes_market.py
```

## Project Structure Philosophy

This project follows **Domain-Driven Design** (DDD) principles:

1. **Domain Layer** (`domains/`) - Contains business logic, isolated from infrastructure
   - Pure business rules and domain models
   - No knowledge of HTTP, databases, or external APIs
   - Testable without mocking infrastructure

2. **Gateway Layer** (`gateway/`) - Infrastructure concerns
   - Caching, health checks, WebSocket management
   - Response formatting and middleware
   - Shared infrastructure services

3. **Routes Layer** (`routes_*.py`) - HTTP API endpoints
   - Thin controllers that delegate to domain services
   - Request/response transformation
   - HTTP-specific concerns (status codes, headers)

4. **Database Layer** (`database/`) - Data persistence
   - SQLAlchemy models and session management
   - Database migrations

**Dependency Flow**: Routes → Domain Services → Infrastructure (DB, Cache, Kafka)

This architecture ensures:
- **Maintainability**: Clear separation of concerns
- **Testability**: Domain logic testable without infrastructure
- **Scalability**: Easy to add new domains or swap infrastructure
- **Type Safety**: Full mypy strict mode compliance
