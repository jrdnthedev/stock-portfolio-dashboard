# Integration Tests

This directory contains integration tests for the Stock Portfolio Dashboard API using **testcontainers** to provide isolated, reproducible test environments. # noqa E999

## Overview

The integration tests use **testcontainers-python** to automatically spin up a PostgreSQL database in a Docker container for testing. This ensures:

- **Isolation**: Each test session gets a fresh database
- **Reproducibility**: Tests run in the same environment everywhere
- **Real Integration**: Tests use actual database interactions, not mocks
- **Fast Cleanup**: Containers are automatically removed after tests

## Prerequisites

Before running the integration tests, ensure you have:

1. **Docker** installed and running
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) for Windows/macOS
   - Docker Engine for Linux

2. **Python 3.11+** with dependencies installed:
   ```powershell
   pip install -r requirements.txt
   ```

## Project Structure

```
tests/
├── conftest_integration.py        # testcontainers configuration
├── integration_test_portfolio.py  # Portfolio endpoint integration tests
├── integration_test_market.py     # Market data endpoint integration tests
├── conftest.py                    # General pytest configuration
├── test_*.py                      # Unit tests (existing)
```

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

- `postgres_container`: PostgreSQL testcontainer (persists for all tests)
- `test_engine`: SQLAlchemy engine connected to test database

### Function-Scoped Fixtures

- `db_session`: Fresh database session for each test (auto-rollback)
- `client`: FastAPI TestClient with database dependency override
- `disable_cache`: Mock cache service to avoid Redis dependency

### Data Fixtures

- `sample_tickers`: Pre-populated ticker data
- `sample_portfolio`: Pre-populated portfolio
- `sample_holdings`: Pre-populated holdings
- `market_tickers`: Market data tickers
- `sample_price_data`: Historical price data

## Architecture

### Testcontainers Configuration

The `conftest_integration.py` file configures testcontainers using pytest fixtures:

1. **Container Lifecycle**: PostgreSQL container starts once per test session
2. **Schema Creation**: Tables are created from SQLAlchemy models
3. **Transaction Management**: Each test runs in a transaction that's rolled back
4. **Dependency Override**: FastAPI's `get_db` dependency is overridden with test session

### Test Isolation

Each test function:
1. Gets a fresh database session
2. Uses a transaction that's rolled back after the test
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
