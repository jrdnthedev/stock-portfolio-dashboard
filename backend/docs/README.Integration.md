# Integration Tests

> Integration tests for the Stock Portfolio Dashboard API using testcontainers for isolated, reproducible test environments.

📚 **[Documentation Index](README.md)** | 🏠 **[Main README](../README.md)**

---

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

The integration tests use **testcontainers-python** to automatically spin up a PostgreSQL database in a Docker container for testing. This ensures:

- **Isolation**: Each test session gets a fresh database
- **Reproducibility**: Tests run in the same environment everywhere
- **Real Integration**: Tests use actual database interactions, not mocks
- **Fast Cleanup**: Containers are automatically removed after tests
- **No Docker Dependency for Unit Tests**: Integration tests only run when Docker is available

## Current Status

✅ **315 Total Tests**: 270 unit tests + 45 integration tests
- Unit tests run without Docker (mocked dependencies)
- Integration tests require Docker running
- Tests automatically skip if Docker unavailable

## Prerequisites

Before running the integration tests, ensure you have:

1. **Docker** installed and running
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) for Windows/macOS
   - Docker Engine for Linux
   - **Note**: Integration tests will be automatically skipped if Docker is not available

2. **Python 3.11+** with dependencies installed:
   ```powershell
   pip install -r requirements.txt
   ```

## Project Structure

```
tests/
├── conftest.py                    # Pytest configuration with test app (no Kafka/Redis)
├── integration_test_portfolio.py  # Portfolio endpoint integration tests (22 tests)
├── integration_test_market.py     # Market data endpoint integration tests (23 tests)
├── test_*.py                      # Unit tests (270 tests)
```

**Note**: The `conftest_integration.py` file has been removed. All test configuration is now in `conftest.py`.

## Running Integration Tests

### Run All Integration Tests

```powershell
# From the backend directory
pytest tests/integration_test_*.py -v
```

### Run Specific Test File

```powershell
# Portfolio tests only
pytest tests/integration_test_portfolio.py -v

# Market tests only
pytest tests/integration_test_market.py -v
```

### Run Specific Test Class or Method

```powershell
# Run a specific test class
pytest tests/integration_test_portfolio.py::TestGetPortfolioIntegration -v

# Run a specific test method
pytest tests/integration_test_portfolio.py::TestGetPortfolioIntegration::test_get_portfolio_success -v
```

### Run with Coverage

```powershell
pytest tests/integration_test_*.py --cov=backend --cov-report=html
```

### Run in Parallel (faster execution)

```powershell
# Install pytest-xdist first
pip install pytest-xdist

# Run tests in parallel
pytest tests/integration_test_*.py -n auto
```

## Test Coverage

### Portfolio Endpoints (`integration_test_portfolio.py`)

#### ✅ GET /v1/portfolio/{id}
- Successfully retrieve portfolio from database
- Handle non-existent portfolio (404)

#### ✅ GET /v1/portfolio/{id}/holdings
- Retrieve all holdings for a portfolio
- Handle empty portfolio
- Handle non-existent portfolio (404)

#### ✅ POST /v1/portfolio/{id}/holdings
- Create new holding with valid data
- Validate quantity constraints
- Handle invalid ticker symbol (404)
- Handle non-existent portfolio (404)
- Invalidate caches after creation

#### ✅ PUT /v1/portfolio/{id}/holdings/{hid}
- Update holding quantity and average cost
- Partial updates (only quantity or only cost)
- Handle non-existent holding (404)
- Invalidate caches after update

#### ✅ DELETE /v1/portfolio/{id}/holdings/{hid}
- Delete holding from database
- Verify deletion in database
- Handle non-existent holding (404)
- Handle non-existent portfolio (404)
- Invalidate caches after deletion

#### ✅ GET /v1/portfolio/{id}/performance
- Retrieve performance metrics
- Filter by date range (from, to)
- Handle non-existent portfolio (404)

#### ✅ GET /v1/portfolio/{id}/allocation
- Retrieve allocation breakdown
- Calculate correct percentages
- Handle empty portfolio
- Handle non-existent portfolio (404)

### Market Data Endpoints (`integration_test_market.py`)

#### ✅ GET /v1/market/prices/{ticker}
- Retrieve historical price data from database
- Filter by date range (from, to)
- Filter by from date only
- Filter by to date only
- Case-insensitive ticker symbol
- Handle non-existent ticker (404)
- Handle ticker with no price data

#### ✅ GET /v1/market/prices/{ticker}/latest
- Retrieve latest price for ticker
- Case-insensitive ticker symbol
- Handle non-existent ticker (404)
- Handle ticker with no price data (404)

#### ✅ GET /v1/market/fundamentals/{ticker}
- Retrieve fundamental data
- Case-insensitive ticker symbol
- Handle non-existent ticker (404)

#### ✅ GET /v1/market/tickers
- Retrieve all tickers
- Filter by sector
- Filter by exchange
- Filter by asset class
- Multiple filters combined
- Case-insensitive filters
- Handle no matches
- Handle empty database

#### ✅ Edge Cases
- Invalid date formats (422)
- From date after to date
- Empty database scenarios

## Fixtures

### Session-Scoped Fixtures

- `postgres_container`: PostgreSQL testcontainer (persists for all integration tests)
- `test_engine`: SQLAlchemy engine connected to test database
- `test_lifespan`: No-op async context manager (replaces main app lifespan to avoid Kafka/Redis dependencies)

### Function-Scoped Fixtures

- `db_session`: Fresh database session for each test (auto-rollback after test)
- `client`: FastAPI TestClient with:
  - Test-specific lifespan handler (no background services)
  - Database dependency override pointing to test database
  - All routes registered (market, portfolio, websocket)
- `disable_cache`: Mock cache service (returns None on get, no-op on set/delete)

### Data Fixtures

- `sample_tickers`: Pre-populated ticker data with sectors and exchanges
- `sample_portfolio`: Pre-populated portfolio (portfolio_id=1)
- `sample_holdings`: Pre-populated holdings linked to portfolio
- `market_tickers`: Market data tickers for market endpoint tests
- `sample_price_data`: Historical price data for date range filtering tests

## Architecture

### Test App Configuration

The `conftest.py` file creates a test-specific FastAPI app:

```python
@pytest.fixture
def test_lifespan():
    """No-op lifespan for tests - avoids starting Kafka/Redis background services."""
    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        yield
    return _lifespan

@pytest.fixture
def client(test_lifespan, db_session):
    """FastAPI test client with database override."""
    # Create test app with no-op lifespan
    test_app = FastAPI(lifespan=test_lifespan)

    # Add middleware
    test_app.add_middleware(RequestLoggingMiddleware)

    # Include all routers
    test_app.include_router(market_router)
    test_app.include_router(portfolio_router)
    test_app.include_router(websocket_router)

    # Override database dependency
    test_app.dependency_overrides[get_db] = lambda: db_session

    return TestClient(test_app)
```

**Key Design Decisions**:
1. **Separate test app**: Avoids starting PricePublisher and PriceEventConsumer
2. **No Kafka/Redis required**: Tests focus on HTTP endpoints and database
3. **Dependency injection**: Database sessions scoped to each test
4. **Automatic rollback**: Each test transaction is rolled back

### Container Lifecycle

1. **Startup** (once per session):
   - PostgreSQL testcontainer starts
   - SQLAlchemy engine connects to container
   - Database schemas created from models

2. **Per Test**:
   - New database session with transaction
   - Test executes with isolated data
   - Transaction rolled back (cleanup)

3. **Shutdown** (end of session):
   - PostgreSQL container stopped and removed
   - Temporary volumes cleaned up
3. Ensures no data persistence between tests
4. Avoids test interdependencies

### Cache Handling

The `disable_cache` fixture mocks the Redis cache service to:
- Avoid external dependencies during integration tests
- Focus testing on database interactions
- Prevent cache-related test flakiness

## Troubleshooting

### Docker Not Running

**Error**: `Cannot connect to the Docker daemon`

**Solution**: Ensure Docker Desktop is running

```powershell
# Check Docker status
docker ps
```

### Port Conflicts

**Error**: `Port 5432 already in use`

**Solution**: Testcontainers automatically assigns random ports. If you have other containers, they won't conflict.

### Slow Test Execution

**Cause**: Container startup takes a few seconds

**Solutions**:
- Container is reused for all tests in a session (session scope)
- Use pytest-xdist for parallel execution
- Run specific test files instead of entire suite

### Database Schema Issues

**Error**: `relation "portfolios" does not exist`

**Solution**: Ensure SQLAlchemy models are imported correctly in conftest_integration.py

```python
from backend.database.models import Base
Base.metadata.create_all(bind=engine)
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'testcontainers'`

**Solution**: Install dependencies

```powershell
pip install -r requirements.txt
```

## Best Practices

### Writing New Integration Tests

1. **Use fixtures for test data**: Don't create data manually in each test
2. **Test real database interactions**: Focus on actual database behavior
3. **Verify database state**: Check data is persisted/deleted correctly
4. **Test error cases**: 404s, validation errors, edge cases
5. **Keep tests independent**: Don't rely on test execution order

### Example Test Pattern

```python
def test_create_resource(
    client: TestClient,
    db_session: Session,
    sample_data: SomeModel,
    disable_cache,
):
    """Test description."""
    # Arrange: Set up test data (via fixtures)
    create_data = {"field": "value"}

skip     # Act: Make API request
    response = client.post("/api/resource", json=create_data)

    # Assert: Verify response
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True

    # Assert: Verify database state
    created_resource = db_session.query(SomeModel).filter_by(field="value").first()
    assert created_resource is not None
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration_test_*.py -v --cov=backend
```

## Performance Considerations

- **Container startup**: ~5-10 seconds (one-time per session)
- **Test execution**: ~0.1-0.5 seconds per test
- **Total suite**: ~30-60 seconds for all integration tests

## Additional Resources

- [Testcontainers Python Documentation](https://testcontainers-python.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

## Contributing

When adding new API endpoints:

1. Create corresponding integration tests
2. Follow existing test patterns
3. Add fixtures for test data
4. Test happy path and error cases
5. Verify database state changes
6. Update this README with new test coverage

---

## See Also

- **[Domain Architecture](README.Domains.md)** - Testing domain services
- **[Authentication](README.Auth.md)** - Testing protected endpoints
- **[Cache Service](README.Cache.md)** - Testing cached responses

---

**Last Updated**: April 2026
**Component**: Testing Infrastructure
**Test Suite**: `backend/tests/integration_test_*.py`
