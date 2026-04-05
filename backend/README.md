# Stock Portfolio Dashboard - Backend API

FastAPI backend for the Stock Portfolio Dashboard application providing real-time market data, portfolio management, and performance analytics. # noqa: E999

## Architecture Overview

The backend follows a **Domain-Driven Design** (DDD) approach with clear separation of concerns:

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Application configuration and settings
├── routes.py               # Stock API routes (legacy)
├── routes_market.py        # Market data API routes
├── routes_portfolio.py     # Portfolio management API routes
│
├── database/               # Database layer
│   ├── database.py         # SQLAlchemy engine and session management
│   └── models.py           # Database models (SQLAlchemy ORM)
│
├── domains/                # Domain business logic
│   ├── market_data/        # Market data domain
│   │   ├── models/         # Domain models
│   │   └── service/        # Market data services
│   │       ├── market_data_service.py    # Core market data orchestration
│   │       ├── pricing_adapter.py        # External pricing API integration
│   │       ├── fundamentals_adapter.py   # Fundamentals data integration
│   │       └── price_publisher.py        # Kafka price publishing
│   └── portfolio/          # Portfolio management domain
│       ├── models/         # Portfolio domain models
│       └── services/       # Portfolio services
│           ├── portfolio_service.py      # Portfolio CRUD operations
│           ├── performance_calculator.py # Performance metrics calculation
│           ├── snapshot_service.py       # Portfolio snapshots
│           └── price_event_consumer.py   # Kafka price event consumer
│
├── gateway/                # Gateway/infrastructure layer
│   ├── cache.py            # Redis caching service
│   ├── formatter.py        # Response envelope formatting
│   ├── health.py           # Health check monitoring
│   └── websocket_manager.py # WebSocket connection management
│
├── middleware/             # HTTP middleware
│   ├── auth.py             # Authentication middleware
│   └── logging.py          # Request logging middleware
│
├── websocket_handler/      # WebSocket handlers
│   ├── handler.py          # WebSocket message handlers
│   └── connection_store.py # Active connection management
│
├── seed/                   # Database seeding
│   ├── seed_data.py        # Seed data definitions
│   ├── seed_database.py    # Database seeding logic
│   └── run_seed.py         # Seed script entry point
│
├── tests/                  # Unit and integration tests
└── docs/                   # Detailed documentation
    ├── README.CodeQuality.md
    ├── README.Docker.md
    ├── README.Cache.md
    ├── README.Formatter.md
    ├── README.Health.md
    ├── README.WebSocket.md
    └── README.Domains.md
```

## Key Features

- **RESTful API** with standardized response envelopes
- **Real-time updates** via WebSocket connections
- **Health monitoring** for PostgreSQL, Redis, and Kafka
- **Request tracing** with UUID-based correlation IDs
- **Caching layer** using Redis for performance optimization
- **Event-driven architecture** with Kafka for price updates
- **Domain-driven design** for maintainable business logic

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
- `GET /` - Root endpoint
- `GET /api/health` - Health check (PostgreSQL, Redis, Kafka)
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Market Data (`/v1/market`)
- `GET /v1/market/prices/{ticker}` - Historical price data (OHLCV)
  - Query: `?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /v1/market/prices/{ticker}/latest` - Latest price quote
- `GET /v1/market/fundamentals/{ticker}` - Company fundamentals
- `GET /v1/market/tickers` - List available tickers
  - Query: `?sector=&exchange=&asset_class=`

### Portfolio Management (`/v1/portfolio`)
- `GET /v1/portfolio/{id}` - Portfolio details
- `GET /v1/portfolio/{id}/holdings` - Portfolio holdings
- `GET /v1/portfolio/{id}/performance` - Performance metrics
  - Query: `?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /v1/portfolio/{id}/allocation` - Asset allocation breakdown
- `POST /v1/portfolio/{id}/holdings` - Add holding to portfolio
- `PUT /v1/portfolio/{id}/holdings/{hid}` - Update holding
- `DELETE /v1/portfolio/{id}/holdings/{hid}` - Remove holding

### Stocks (Legacy) (`/api/stocks`)
- `GET /api/stocks` - List all stocks
- `GET /api/stocks/{symbol}` - Get stock by symbol

All responses follow a standardized envelope format with:
- `success`: boolean
- `data`: response payload
- `message`: human-readable message
- `errors`: error details (if applicable)
- `metadata`: additional context (pagination, filters, etc.)
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

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_market_routes.py

# Run with verbose output
pytest -v
```

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
