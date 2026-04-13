# Dependency Injection Framework Guide

**Implementation Date:** April 11, 2026
**Framework:** Pure-Python Lightweight DI Container

---

## Overview

The backend uses a custom lightweight dependency injection container for centralized dependency management. This provides:

✅ **Testability** - Easy to swap implementations for testing
✅ **Configuration** - Centralized dependency wiring
✅ **Lifecycle** - Proper singleton/factory management
✅ **Type Safety** - Full type checking support
✅ **No Build Dependencies** - Pure Python, no C compiler needed

---

## Container Structure

All dependencies are configured in [backend/container.py](../container.py):

```python
class Container:
    """Lightweight dependency injection container."""

    @property
    def config(self) -> Settings:
        """Get application settings (singleton)."""

    @property
    def db_engine(self):
        """Get database engine (singleton)."""

    @property
    def db_session_factory(self):
        """Get database session factory (singleton)."""

    def get_db_session(self) -> Generator[Session, None, None]:
        """Create a database session (factory)."""

    def get_portfolio_service(self, session: Session) -> PortfolioService:
        """Create a portfolio service with all dependencies (factory)."""
```

---

## Usage in Routes

### Option 1: Traditional Manual DI (Current)

This approach continues to work without changes:

```python
from backend.api.dependencies import get_portfolio_service

@router.post("/portfolios")
def create_portfolio(
    service: PortfolioService = Depends(get_portfolio_service)
):
    return service.create_portfolio(...)
```

### Option 2: Container-Based DI (Recommended)

Use the container for centralized dependency management:

```python
from backend.api.dependencies import get_portfolio_service_from_container

@router.post("/portfolios")
def create_portfolio(
    service: PortfolioService = Depends(get_portfolio_service_from_container)
):
    return service.create_portfolio(...)
```

### Option 3: Direct Container Access

For advanced use cases:

```python
from backend.api.dependencies import get_container

@router.get("/portfolios")
def list_portfolios(
    db: Session = Depends(get_db),
    container: Container = Depends(get_container)
):
    service = container.get_portfolio_service(db)
    return service.list_portfolios()
```

---

## Lifecycle Management

### Singleton Pattern

Properties are lazily initialized and cached:

```python
@property
def config(self) -> Settings:
    if self._config is None:
        self._config = get_settings()
    return self._config
```

**Use for:** Configuration, database engines, shared resources

### Factory Pattern

Methods create new instances each time:

```python
def get_portfolio_service(self, session: Session) -> PortfolioService:
    portfolio_repo = self.get_portfolio_repository(session)
    holding_repo = self.get_holding_repository(session)
    return PortfolioService(portfolio_repo, holding_repo, ...)
```

**Use for:** Repositories, services that need fresh state

---

## Testing with the Container

### Mock Dependencies in Tests

```python
from unittest.mock import Mock
from backend.container import Container

def test_create_portfolio():
    # Create a test container
    container = Container()

    # Create mock session
    mock_session = Mock()

    # Get service with mocked dependencies
    service = container.get_portfolio_service(mock_session)

    # Mock the repositories if needed
    service.portfolio_repo = Mock()
    service.holding_repo = Mock()

    # Test
    result = service.create_portfolio("Test", "owner1")
    assert result.name == "Test"

    # Reset container
    container.reset()
```

### Override Container Methods

```python
from backend.container import Container

class TestContainer(Container):
    """Test container with overridden dependencies."""

    def get_portfolio_repository(self, session):
        return MockPortfolioRepository()

    def get_holding_repository(self, session):
        return MockHoldingRepository()


def test_with_custom_container():
    container = TestContainer()
    session = Mock()
    service = container.get_portfolio_service(session)
    # Service now uses mock repositories
```

### Integration Tests

```python
import pytest
from backend.container import Container

@pytest.fixture
def container(test_db_session):
    """Create a container with test database."""
    container = Container()
    yield container
    container.reset()


def test_integration(container, test_db_session):
    service = container.get_portfolio_service(test_db_session)
    # Test with real database (testcontainers)
    portfolio = service.create_portfolio("Test Portfolio", "owner1")
    assert portfolio.name == "Test Portfolio"
```

---

## Adding New Dependencies

### 1. Add Method to Container

```python
# In backend/container.py
class Container:
    # ... existing methods

    def get_market_data_service(self, session: Session) -> MarketDataService:
        """Create a market data service with all dependencies (factory)."""
        pricing_adapter = PricingAdapter(self.config)
        fundamentals_adapter = FundamentalsAdapter(self.config)

        return MarketDataService(
            pricing_adapter=pricing_adapter,
            fundamentals_adapter=fundamentals_adapter,
            cache_service=self.get_cache_service(),
        )
```

### 2. Create Dependency Helper

```python
# In backend/api/dependencies.py
def get_market_data_service(
    db: Session = Depends(get_db),
    container: Container = Depends(get_container),
) -> MarketDataService:
    """Get MarketDataService from container."""
    return container.get_market_data_service(db)
```

### 3. Use in Routes

```python
from backend.api.dependencies import get_market_data_service

@router.get("/market/data")
def get_market_data(
    service: MarketDataService = Depends(get_market_data_service)
):
    return service.get_data()
```

---

## Configuration Management

### Environment-Specific Settings

The container uses `get_settings()` which returns a `Settings` instance based on environment variables:

```python
# Development (.env)
DATABASE_URL=postgresql://localhost/dev_db
DEBUG=true

# Production (.env.prod)
DATABASE_URL=postgresql://prod-server/prod_db
DEBUG=false
```

### Accessing Configuration

```python
# In a service
class MyService:
    def __init__(self, config: Settings):
        self.api_key = config.stock_api_key

# In container
def get_my_service(self) -> MyService:
    return MyService(config=self.config)
```

---

## Best Practices

### 1. Use Factory Methods for Stateful Services

```python
# ✅ Good - Creates new instance per request
def get_portfolio_service(self, session: Session) -> PortfolioService:
    return PortfolioService(...)

# ❌ Bad - Shared state between requests (use property instead)
@property
def portfolio_service(self) -> PortfolioService:
    if self._portfolio_service is None:
        self._portfolio_service = PortfolioService(...)
    return self._portfolio_service
```

### 2. Use Singleton for Stateless/Expensive Resources

### 2. Use Properties for Expensive Shared Resources

```python
# ✅ Good - Reuse expensive connection (property with caching)
@property
def db_engine(self):
    if self._db_engine is None:
        self._db_engine = create_engine(...)
    return self._db_engine

# ❌ Bad - Creates new engine per request
def get_db_engine(self):
    return create_engine(...)
```

### 3. Explicit Dependencies Over Globals

```python
# ✅ Good - Explicit dependency
class PortfolioService:
    def __init__(self, repo: PortfolioRepository):
        self.repo = repo

# ❌ Bad - Hidden global dependency
class PortfolioService:
    def __init__(self):
        self.repo = global_repository
```

### 4. Use Type Hints

```python
# ✅ Good - Type checker can validate
service: PortfolioService = Depends(get_portfolio_service)

# ❌ Bad - No type checking
service = Depends(get_portfolio_service)
```

---

## Migration Path

### Phase 1: ✅ Complete (April 11, 2026)
- [x] Create pure-Python `Container` in `backend/container.py`
- [x] Add container to app state in `main.py`
- [x] Create helper functions in `api/dependencies.py`
- [x] Maintain backwards compatibility with existing code

### Phase 2: Gradual Adoption
- [ ] Migrate routes one-by-one to use container-based DI
- [ ] Update tests to use container
- [ ] Add more services to container (market data, alerts, etc.)

### Phase 3: Simplify and Optimize
- [ ] Remove redundant manual dependency wiring
- [ ] Add more factory methods to container
- [ ] Update documentation with real-world examples

---

## Troubleshooting

### Container Not Found in App State

**Problem:** `AttributeError: 'State' object has no attribute 'services'`

**Solution:** Ensure the container is initialized in lifespan:
```python
# In main.py
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    container = Container()
    _app.state.services = AppState(container=container, ...)
    yield
```

### Database Session Issues

**Problem:** Sessions not being closed properly

**Solution:** Use the container's `get_db_session()` generator:
```python
def some_operation():
    container = Container()
    for session in container.get_db_session():
        # Use session
        result = session.query(...)
    # Session automatically closed after loop
```

### Testing with Mock Dependencies

**Problem:** Hard to inject mocks

**Solution:** Create a test subclass:
```python
class TestContainer(Container):
    def get_portfolio_repository(self, session):
        return MockPortfolioRepository()
```

---

## References

- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Python Property Decorator](https://docs.python.org/3/library/functions.html#property)
- [Architecture Recommendations](ARCHITECTURE_RECOMMENDATIONS.md#5-dependency-injection-framework)

---

## Examples

### Example 1: Simple Service

```python
# Define service
class NotificationService:
    def __init__(self, email_adapter: EmailAdapter):
        self.email = email_adapter

    def send_alert(self, message: str):
        self.email.send(message)

# Add to container
class Container:
    # ... existing methods

    def get_notification_service(self) -> NotificationService:
        email_adapter = EmailAdapter(self.config)
        return NotificationService(email_adapter=email_adapter)

# Use in route
from backend.api.dependencies import get_container

@router.post("/alerts")
def send_alert(
    message: str,
    container: Container = Depends(get_container)
):
    service = container.get_notification_service()
    service.send_alert(message)
    return {"status": "sent"}
```

### Example 2: Service with Configuration

```python
# Service with config
class CacheService:
    def __init__(self, config: Settings):
        self.redis = Redis(
            host=config.redis_host,
            port=config.redis_port,
        )

# Add to container as cached property
class Container:
    @property
    def cache_service(self) -> CacheService:
        if not hasattr(self, '_cache_service'):
            self._cache_service = CacheService(config=self.config)
        return self._cache_service
```

### Example 3: Chained Dependencies

```python
# Multiple levels of dependencies
class Container:
    def get_pricing_adapter(self) -> PricingAdapter:
        return PricingAdapter(self.config)

    def get_fundamentals_adapter(self) -> FundamentalsAdapter:
        return FundamentalsAdapter(self.config)

    def get_market_data_service(self) -> MarketDataService:
        pricing = self.get_pricing_adapter()
        fundamentals = self.get_fundamentals_adapter()
        cache = self.cache_service  # Uses cached singleton

        return MarketDataService(
            pricing=pricing,
            fundamentals=fundamentals,
            cache=cache,
        )
```

### Example 4: Service with Session Dependency

```python
# Service that needs database session
def get_analytics_service(
    db: Session = Depends(get_db),
    container: Container = Depends(get_container)
) -> AnalyticsService:
    """Get analytics service with database session."""
    portfolio_repo = container.get_portfolio_repository(db)
    holdings_repo = container.get_holding_repository(db)

    return AnalyticsService(
        portfolio_repo=portfolio_repo,
        holdings_repo=holdings_repo,
        config=container.config,
    )

# Use in route
@router.get("/analytics/{portfolio_id}")
def get_analytics(
    portfolio_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service)
):
    return service.calculate_metrics(portfolio_id)
```
