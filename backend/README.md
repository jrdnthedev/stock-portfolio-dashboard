# Stock Portfolio Dashboard - Backend API

FastAPI backend for the Stock Portfolio Dashboard application providing real-time market data, portfolio management, and performance analytics. # noqa: E999

## Architecture Overview

The backend follows a **Domain-Driven Design** (DDD) approach with clear separation of concerns:

```
backend/
├── main.py                 # FastAPI application entry point with lifespan handlers
├── config.py               # Application configuration and settings
├── routes_market.py        # Market data API routes (/v1/market)
├── routes_portfolio.py     # Portfolio management API routes (/v1/portfolio)
├── routes_websocket.py     # WebSocket routes for real-time updates (/ws)
│
├── database/               # Database layer
│   ├── database.py         # SQLAlchemy engine and session management
│   └── models.py           # Database models (SQLAlchemy ORM)
│
├── domains/                # Domain business logic (DDD)
│   ├── market_data/        # Market data domain
│   │   ├── models/         # Domain models (Price, Ticker)
│   │   │   └── models.py
│   │   └── service/        # Market data services
│   │       ├── market_data_service.py    # Core market data orchestration
│   │       ├── pricing_adapter.py        # Mock price generation & Kafka publishing
│   │       ├── fundamentals_adapter.py   # Fundamentals data integration
│   │       └── price_publisher.py        # Background price publisher (5s interval)
│   └── portfolio/          # Portfolio management domain
│       ├── models/         # Portfolio domain models
│       │   └── models.py
│       └── services/       # Portfolio services
│           ├── portfolio_service.py      # Portfolio CRUD operations with Kafka
│           ├── performance_calculator.py # Real-time P&L calculation
│           ├── snapshot_service.py       # Portfolio snapshots
│           └── price_event_consumer.py   # Kafka consumer & orchestrator
│
├── gateway/                # Gateway/infrastructure layer
│   ├── cache.py            # Redis caching service
│   ├── formatter.py        # Response envelope formatting
│   ├── health.py           # Health check monitoring (PostgreSQL, Redis, Kafka)
│   └── websocket_manager.py # Redis-backed WebSocket manager
│
├── middleware/             # HTTP middleware
│   ├── auth.py             # Authentication middleware (planned)
│   └── logging.py          # Request logging with correlation IDs
│
├── websocket_handler/      # WebSocket handlers
│   ├── handler.py          # WebSocket message handlers (planned)
│   └── connection_store.py # Active connection management (planned)
│
├── seed/                   # Database seeding
│   ├── seed_data.py        # Seed data definitions
│   ├── seed_database.py    # Database seeding logic
│   └── run_seed.py         # Seed script entry point
│
├── tests/                  # Unit and integration tests (315 tests)
│   ├── conftest.py         # Pytest configuration and fixtures
│   ├── test_*.py           # Unit tests (270 tests)
│   └── integration_test_*.py # Integration tests with testcontainers (45 tests)
│
└── docs/                   # Detailed documentation
    ├── README.Cache.md         # Redis caching strategies
    ├── README.Formatter.md     # Response envelope patterns
    ├── README.Health.md        # Health check implementation
    ├── README.WebSocket.md     # WebSocket real-time updates
    ├── README.Domains.md       # Domain-driven design guide
    └── README.Integration.md   # Integration testing guide
```

## Key Features

### Core Functionality
- **RESTful API** with standardized response envelopes (success, data, message, errors, metadata, timestamp)
- **Real-time updates** via WebSocket with Redis-backed connection registry
- **Event-driven architecture** with Kafka for price streaming and portfolio updates
- **Domain-driven design** with clear separation between business logic and infrastructure

### Background Services (Lifespan Handlers)
- **PricePublisher**: Publishes mock price events every 5 seconds to `market.prices.live` Kafka topic
- **PriceEventConsumer**: Consumes price events and triggers portfolio recalculation
- **PortfolioPerformanceOrchestrator**: Coordinates price updates with P&L calculations and WebSocket broadcasts

### Infrastructure
- **Health monitoring** for PostgreSQL, Redis, and Kafka with detailed status reporting
- **Request tracing** with UUID-based correlation IDs in all requests
- **Caching layer** using Redis with intelligent TTL strategies and cache invalidation
- **WebSocket manager** with topic-based subscriptions for real-time portfolio updates
- **Request logging** middleware with correlation IDs and performance metrics

## Technology Stack

- **Framework**: FastAPI 0.115.0
- **Database**: PostgreSQL with SQLAlchemy 2.0.36
- **Cache**: Redis 5.0.1
- **Message Broker**: Kafka (kafka-python-ng 2.2.2)
- **Validation**: Pydantic 2.9.2
- **Type Checking**: mypy (strict mode)
- **Testing**: pytest
- **ASGI Server**: uvicorn

## Setup

1. **Activate the virtual environment:**
   ```bash
   .\.venv\Scripts\activate  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env` and update with your API keys

4. **Run the development server:**
   ```bash
   python main.py
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Health & Documentation
- `GET /` - Root endpoint with API status
- `GET /api/health` - Comprehensive health check (PostgreSQL, Redis, Kafka)
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Market Data (`/v1/market`)
- `GET /v1/market/prices/{ticker}` - Historical OHLCV price data
  - Query params: `from=YYYY-MM-DD`, `to=YYYY-MM-DD`
  - Returns: Array of PricePoint objects with open, high, low, close, volume
- `GET /v1/market/prices/{ticker}/latest` - Latest price quote
  - Returns: Current price, change, change_percent, volume, timestamp
- `GET /v1/market/fundamentals/{ticker}` - Company fundamentals
  - Returns: Company name, sector, industry, market cap, P/E, EPS
- `GET /v1/market/tickers` - List available tickers with filtering
  - Query params: `sector`, `exchange`, `asset_class`
  - Supports case-insensitive filtering

### Portfolio Management (`/v1/portfolio`)
- `GET /v1/portfolio/{id}` - Get portfolio details
  - Returns: Portfolio with name, description, created/updated timestamps
- `GET /v1/portfolio/{id}/holdings` - Get all portfolio holdings
  - Returns: Array of holdings with ticker, quantity, average_cost, P&L metrics
- `GET /v1/portfolio/{id}/performance` - Get portfolio performance metrics
  - Query params: `from=YYYY-MM-DD`, `to=YYYY-MM-DD` (optional date filtering)
  - Returns: Total value, cost, unrealized P&L, return percentage, holdings breakdown
- `GET /v1/portfolio/{id}/allocation` - Get asset allocation breakdown
  - Returns: Allocation by sector with weights and values
- `POST /v1/portfolio/{id}/holdings` - Add new holding
  - Body: `{ticker: str, quantity: int, average_cost: float}`
  - Publishes `portfolio.holdings.changed` event to Kafka
  - Invalidates portfolio and performance caches
- `PUT /v1/portfolio/{id}/holdings/{hid}` - Update existing holding
  - Body: `{quantity?: int, average_cost?: float}`
  - Supports partial updates
  - Publishes Kafka event and invalidates caches
- `DELETE /v1/portfolio/{id}/holdings/{hid}` - Delete holding
  - Publishes Kafka event and invalidates caches

### WebSocket (`/ws`)
- `WS /ws/portfolio?client_id={uuid}` - Real-time portfolio updates
  - Client messages: `subscribe`, `unsubscribe`, `ping`
  - Server messages: Portfolio performance updates, subscription confirmations
- `GET /ws/status` - WebSocket connection statistics
  - Returns: Active connection count, connected client IDs

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
    "correlation_id": "uuid"
  },
  "timestamp": "2026-04-07T10:30:00Z"
}
```

**Envelope Fields:**
- `success`: Boolean indicating request success
- `data`: Response payload (null on error)
- `message`: Human-readable status message
- `errors`: Array of error details (null on success)
- `metadata`: Additional context (filters, pagination, correlation_id)
- `timestamp`: ISO 8601 timestamp

## Development

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Documentation

Detailed documentation is available in the `docs/` folder:

### Infrastructure & Gateway
- **[Cache Service](docs/README.Cache.md)** - Redis caching implementation, TTL strategies, cache invalidation
- **[Response Formatter](docs/README.Formatter.md)** - Standardized response envelopes, error formatting
- **[Health Monitoring](docs/README.Health.md)** - PostgreSQL, Redis, and Kafka health checks
- **[WebSocket Manager](docs/README.WebSocket.md)** - Real-time communication, connection management, topic subscriptions

### Domain Layer
- **[Domains Architecture](docs/README.Domains.md)** - Complete guide to market data and portfolio domains
  - Market Data Services (pricing, fundamentals, publishing)
  - Portfolio Services (CRUD, performance calculation, snapshots)
  - Event-driven architecture with Kafka
  - Caching strategies and error handling

### Development & Deployment
- **[Code Quality](docs/README.CodeQuality.md)** - Type checking, linting, testing standards
- **[Docker Setup](docs/README.Docker.md)** - Containerization and deployment

## Running Tests

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
