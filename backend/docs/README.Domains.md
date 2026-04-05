# Domain Layer Documentation

**Location**: # noqa: E999 `backend/domains/`

## Overview

The domain layer implements business logic using **Domain-Driven Design** (DDD) principles. It consists of two primary domains: **Market Data** and **Portfolio Management**, each with their own models and services.

---

## Architecture Principles

### Domain-Driven Design (DDD)

1. **Separation of Concerns**: Business logic isolated from infrastructure
2. **Ubiquitous Language**: Domain terms used consistently throughout the codebase
3. **Bounded Contexts**: Clear boundaries between domains
4. **Domain Models**: Rich models that encapsulate business rules
5. **Domain Services**: Orchestration of business operations

### Dependency Flow

```
HTTP Routes → Domain Services → Domain Models
                ↓
        Infrastructure (DB, Cache, Kafka)
```

**Key Rule**: Domain layer never imports from routes or HTTP layer.

---

# Market Data Domain

**Location**: `backend/domains/market_data/`

## Purpose

Provides market data retrieval, caching, and real-time distribution for stocks, ETFs, and other securities.

## Structure

```
market_data/
├── models/
│   ├── __init__.py
│   └── models.py              # Domain models (Price, Fundamental, Ticker)
└── service/
    ├── market_data_service.py    # Core orchestration service
    ├── pricing_adapter.py        # External pricing API integration
    ├── fundamentals_adapter.py   # Fundamentals API integration
    └── price_publisher.py        # Kafka price publishing
```

---

## Models

### Location: `market_data/models/models.py`

**Domain Entities**:

```python
class Price(BaseModel):
    """Price data point for a security."""
    ticker: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

class Fundamental(BaseModel):
    """Fundamental data for a company."""
    ticker: str
    company_name: str
    market_cap: Decimal
    pe_ratio: Optional[Decimal]
    dividend_yield: Optional[Decimal]
    eps: Optional[Decimal]
    sector: str
    industry: str

class Ticker(BaseModel):
    """Security ticker information."""
    symbol: str
    name: str
    exchange: str
    asset_class: str  # 'Stock', 'ETF', 'Option', etc.
    sector: Optional[str]
```

---

## Services

### 1. Market Data Service

**Location**: `market_data/service/market_data_service.py`

**Purpose**: Core orchestration service for market data operations.

**Key Methods**:

```python
class MarketDataService:
    """Orchestrates market data retrieval and caching."""

    def __init__(
        self,
        pricing_adapter: PricingAdapter,
        fundamentals_adapter: FundamentalsAdapter,
        cache: CacheService,
        publisher: PricePublisher
    ):
        self.pricing = pricing_adapter
        self.fundamentals = fundamentals_adapter
        self.cache = cache
        self.publisher = publisher

    async def get_latest_price(self, ticker: str) -> Price:
        """
        Get latest price with caching.

        Flow:
        1. Check cache
        2. If miss, fetch from pricing adapter
        3. Cache result (TTL: 30s)
        4. Publish to Kafka for real-time updates
        5. Return price
        """
        cache_key = f"price:latest:{ticker}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return Price.parse_raw(cached)

        # Fetch from external API
        price = await self.pricing.get_latest_price(ticker)

        # Cache and publish
        await self.cache.set(cache_key, price.json(), ttl=30)
        await self.publisher.publish_price(price)

        return price

    async def get_historical_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> List[Price]:
        """
        Get historical OHLCV data.

        Cache TTL: 1 hour (historical data doesn't change)
        """
        cache_key = f"price:history:{ticker}:{start_date}:{end_date}"

        cached = await self.cache.get(cache_key)
        if cached:
            return [Price.parse_raw(p) for p in json.loads(cached)]

        prices = await self.pricing.get_historical_prices(
            ticker, start_date, end_date
        )

        await self.cache.set(
            cache_key,
            json.dumps([p.json() for p in prices]),
            ttl=3600
        )

        return prices

    async def get_fundamentals(self, ticker: str) -> Fundamental:
        """
        Get company fundamentals.

        Cache TTL: 24 hours (fundamentals update daily)
        """
        cache_key = f"fundamentals:{ticker}"

        cached = await self.cache.get(cache_key)
        if cached:
            return Fundamental.parse_raw(cached)

        fundamental = await self.fundamentals.get_fundamentals(ticker)

        await self.cache.set(cache_key, fundamental.json(), ttl=86400)

        return fundamental
```

**Testing**: `backend/tests/test_market_data_service.py`

---

### 2. Pricing Adapter

**Location**: `market_data/service/pricing_adapter.py`

**Purpose**: Integrates with external pricing APIs (Alpha Vantage, Polygon.io, etc.).

**Interface**:

```python
class PricingAdapter:
    """Adapter for external pricing data sources."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def get_latest_price(self, ticker: str) -> Price:
        """
        Fetch latest price quote from external API.

        Error Handling:
        - API rate limit → Raise RateLimitError
        - Ticker not found → Raise TickerNotFoundError
        - API timeout → Raise PricingAPIError
        """
        url = f"{self.base_url}/quote/{ticker}"
        params = {"apikey": self.api_key}

        try:
            response = await self.client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return Price(
                ticker=ticker,
                timestamp=datetime.fromisoformat(data["timestamp"]),
                open=Decimal(data["open"]),
                high=Decimal(data["high"]),
                low=Decimal(data["low"]),
                close=Decimal(data["close"]),
                volume=int(data["volume"])
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise TickerNotFoundError(f"Ticker {ticker} not found")
            elif e.response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")
            else:
                raise PricingAPIError(f"API error: {e}")
        except httpx.TimeoutException:
            raise PricingAPIError(f"Timeout fetching price for {ticker}")

    async def get_historical_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        interval: str = "1day"
    ) -> List[Price]:
        """Fetch historical OHLCV data."""
        # Implementation similar to get_latest_price
        pass
```

**Configuration**:
- API key stored in environment variables
- Base URL configurable per provider
- Timeout: 10 seconds
- Retry logic: 3 attempts with exponential backoff

**Testing**: `backend/tests/test_pricing_adapter.py`

---

### 3. Fundamentals Adapter

**Location**: `market_data/service/fundamentals_adapter.py`

**Purpose**: Fetches company fundamentals (balance sheet, income statement, ratios).

**Interface**:

```python
class FundamentalsAdapter:
    """Adapter for fundamental data sources."""

    async def get_fundamentals(self, ticker: str) -> Fundamental:
        """
        Fetch company fundamentals.

        Sources:
        - Financial Modeling Prep API
        - SEC EDGAR filings
        - Yahoo Finance
        """
        url = f"{self.base_url}/company/{ticker}/fundamentals"

        response = await self.client.get(url, params={"apikey": self.api_key})
        data = response.json()

        return Fundamental(
            ticker=ticker,
            company_name=data["companyName"],
            market_cap=Decimal(data["marketCap"]),
            pe_ratio=Decimal(data["peRatio"]) if data["peRatio"] else None,
            dividend_yield=Decimal(data["dividendYield"]) if data["dividendYield"] else None,
            eps=Decimal(data["eps"]) if data["eps"] else None,
            sector=data["sector"],
            industry=data["industry"]
        )
```

**Testing**: `backend/tests/test_fundamentals_adapter.py`

---

### 4. Price Publisher

**Location**: `market_data/service/price_publisher.py`

**Purpose**: Publishes price updates to Kafka for real-time distribution.

**Interface**:

```python
class PricePublisher:
    """Publishes price updates to Kafka."""

    def __init__(self, bootstrap_servers: str, topic_prefix: str):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic_prefix = topic_prefix

    async def publish_price(self, price: Price) -> None:
        """
        Publish price update to Kafka.

        Topic: {topic_prefix}.prices.{ticker}
        Key: ticker (for partitioning)
        Value: Price JSON
        """
        topic = f"{self.topic_prefix}.prices.{price.ticker}"

        self.producer.send(
            topic,
            key=price.ticker.encode('utf-8'),
            value=price.dict()
        )

        self.producer.flush()
        logger.info(f"Published price for {price.ticker} to {topic}")

    def close(self):
        """Close Kafka producer."""
        self.producer.close()
```

**Topics**:
- `market-data.prices.AAPL` - AAPL price updates
- `market-data.prices.GOOGL` - GOOGL price updates
- etc.

**Testing**: `backend/tests/test_price_publisher.py`

---

# Portfolio Domain

**Location**: `backend/domains/portfolio/`

## Purpose

Manages portfolio operations including CRUD operations, performance calculations, and price event consumption.

## Structure

```
portfolio/
├── models/
│   └── models.py                    # Domain models (Portfolio, Holding, etc.)
└── services/
    ├── __init__.py
    ├── portfolio_service.py         # Portfolio CRUD operations
    ├── performance_calculator.py    # Performance metrics
    ├── snapshot_service.py          # Portfolio snapshots
    └── price_event_consumer.py      # Kafka price event consumer
```

---

## Models

### Location: `portfolio/models/models.py`

**Domain Entities**:

```python
class Portfolio(BaseModel):
    """User's investment portfolio."""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

class Holding(BaseModel):
    """Individual position in a portfolio."""
    id: int
    portfolio_id: int
    ticker: str
    quantity: Decimal
    average_cost: Decimal  # Cost basis per share
    purchased_at: datetime
    updated_at: datetime

    @property
    def total_cost(self) -> Decimal:
        """Total cost basis."""
        return self.quantity * self.average_cost

class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics."""
    portfolio_id: int
    total_value: Decimal
    total_cost: Decimal
    realized_gain: Decimal
    unrealized_gain: Decimal
    total_gain: Decimal
    total_return_percent: Decimal
    time_weighted_return: Decimal
    calculated_at: datetime

class PortfolioSnapshot(BaseModel):
    """Point-in-time portfolio state."""
    id: int
    portfolio_id: int
    total_value: Decimal
    total_cost: Decimal
    gain: Decimal
    gain_percent: Decimal
    holdings_count: int
    snapshot_date: date
    created_at: datetime
```

---

## Services

### 1. Portfolio Service

**Location**: `portfolio/services/portfolio_service.py`

**Purpose**: CRUD operations for portfolios and holdings.

**Key Methods**:

```python
class PortfolioService:
    """Manages portfolio operations."""

    def __init__(self, db_session: Session, cache: CacheService):
        self.db = db_session
        self.cache = cache

    async def create_portfolio(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None
    ) -> Portfolio:
        """Create a new portfolio."""
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)

        # Invalidate user's portfolio list cache
        await self.cache.delete(f"portfolios:user:{user_id}")

        return portfolio

    async def add_holding(
        self,
        portfolio_id: int,
        ticker: str,
        quantity: Decimal,
        average_cost: Decimal
    ) -> Holding:
        """
        Add a holding to a portfolio.

        Business Rules:
        - Quantity must be positive
        - Average cost must be positive
        - Ticker must exist in market data
        - Portfolio must exist and belong to user
        """
        # Validate portfolio exists
        portfolio = self.db.query(Portfolio).filter_by(id=portfolio_id).first()
        if not portfolio:
            raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")

        # Create holding
        holding = Holding(
            portfolio_id=portfolio_id,
            ticker=ticker.upper(),
            quantity=quantity,
            average_cost=average_cost,
            purchased_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

        self.db.add(holding)

        # Update portfolio timestamp
        portfolio.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(holding)

        # Invalidate caches
        await self.cache.delete(f"portfolio:{portfolio_id}:holdings")
        await self.cache.delete(f"portfolio:{portfolio_id}:performance")

        return holding

    async def update_holding(
        self,
        holding_id: int,
        quantity: Optional[Decimal] = None,
        average_cost: Optional[Decimal] = None
    ) -> Holding:
        """Update an existing holding."""
        holding = self.db.query(Holding).filter_by(id=holding_id).first()
        if not holding:
            raise HoldingNotFoundError(f"Holding {holding_id} not found")

        if quantity is not None:
            holding.quantity = quantity
        if average_cost is not None:
            holding.average_cost = average_cost

        holding.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(holding)

        # Invalidate caches
        await self.cache.delete(f"portfolio:{holding.portfolio_id}:holdings")
        await self.cache.delete(f"portfolio:{holding.portfolio_id}:performance")

        return holding

    async def delete_holding(self, holding_id: int) -> None:
        """Remove a holding from portfolio."""
        holding = self.db.query(Holding).filter_by(id=holding_id).first()
        if not holding:
            raise HoldingNotFoundError(f"Holding {holding_id} not found")

        portfolio_id = holding.portfolio_id

        self.db.delete(holding)
        self.db.commit()

        # Invalidate caches
        await self.cache.delete(f"portfolio:{portfolio_id}:holdings")
        await self.cache.delete(f"portfolio:{portfolio_id}:performance")
```

**Testing**: `backend/tests/test_portfolio_service.py`

---

### 2. Performance Calculator

**Location**: `portfolio/services/performance_calculator.py`

**Purpose**: Calculates portfolio performance metrics.

**Key Calculations**:

```python
class PerformanceCalculator:
    """Calculates portfolio performance metrics."""

    def __init__(
        self,
        market_data_service: MarketDataService,
        db_session: Session
    ):
        self.market_data = market_data_service
        self.db = db_session

    async def calculate_portfolio_performance(
        self,
        portfolio_id: int
    ) -> PerformanceMetrics:
        """
        Calculate current portfolio performance.

        Metrics:
        - Total Value: Sum of (quantity × current_price) for all holdings
        - Total Cost: Sum of (quantity × average_cost) for all holdings
        - Unrealized Gain: Total Value - Total Cost
        - Total Return %: (Unrealized Gain / Total Cost) × 100
        """
        holdings = self.db.query(Holding).filter_by(
            portfolio_id=portfolio_id
        ).all()

        total_value = Decimal(0)
        total_cost = Decimal(0)

        for holding in holdings:
            # Fetch current price
            current_price = await self.market_data.get_latest_price(
                holding.ticker
            )

            # Calculate holding value
            holding_value = holding.quantity * current_price.close
            holding_cost = holding.quantity * holding.average_cost

            total_value += holding_value
            total_cost += holding_cost

        unrealized_gain = total_value - total_cost
        total_return_percent = (
            (unrealized_gain / total_cost * 100)
            if total_cost > 0
            else Decimal(0)
        )

        return PerformanceMetrics(
            portfolio_id=portfolio_id,
            total_value=total_value,
            total_cost=total_cost,
            realized_gain=Decimal(0),  # TODO: Track realized gains
            unrealized_gain=unrealized_gain,
            total_gain=unrealized_gain,
            total_return_percent=total_return_percent,
            time_weighted_return=Decimal(0),  # TODO: Implement TWR
            calculated_at=datetime.now(UTC)
        )

    def calculate_time_weighted_return(
        self,
        portfolio_id: int,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """
        Calculate time-weighted return (TWR).

        Formula: TWR = [(1 + r1) × (1 + r2) × ... × (1 + rn)] - 1

        Where ri = (Ending Value - Beginning Value - Cash Flows) /
                   (Beginning Value + Cash Flows)
        """
        # Implementation requires portfolio snapshots
        pass
```

**Testing**: `backend/tests/test_performance_calculator.py`

---

### 3. Snapshot Service

**Location**: `portfolio/services/snapshot_service.py`

**Purpose**: Creates and manages portfolio snapshots for historical analysis.

**Interface**:

```python
class SnapshotService:
    """Manages portfolio snapshots."""

    def __init__(
        self,
        performance_calculator: PerformanceCalculator,
        db_session: Session
    ):
        self.calculator = performance_calculator
        self.db = db_session

    async def create_daily_snapshot(self, portfolio_id: int) -> PortfolioSnapshot:
        """
        Create a snapshot of current portfolio state.

        Scheduled to run daily at market close.
        """
        performance = await self.calculator.calculate_portfolio_performance(
            portfolio_id
        )

        holdings_count = self.db.query(Holding).filter_by(
            portfolio_id=portfolio_id
        ).count()

        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            total_value=performance.total_value,
            total_cost=performance.total_cost,
            gain=performance.unrealized_gain,
            gain_percent=performance.total_return_percent,
            holdings_count=holdings_count,
            snapshot_date=date.today(),
            created_at=datetime.now(UTC)
        )

        self.db.add(snapshot)
        self.db.commit()

        return snapshot

    async def get_performance_history(
        self,
        portfolio_id: int,
        start_date: date,
        end_date: date
    ) -> List[PortfolioSnapshot]:
        """Get historical snapshots for a date range."""
        return self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id,
            PortfolioSnapshot.snapshot_date >= start_date,
            PortfolioSnapshot.snapshot_date <= end_date
        ).order_by(PortfolioSnapshot.snapshot_date).all()
```

**Scheduled Job**: Run daily at 4:30 PM ET (after market close)

**Testing**: `backend/tests/test_snapshot_service.py`

---

### 4. Price Event Consumer

**Location**: `portfolio/services/price_event_consumer.py`

**Purpose**: Consumes price updates from Kafka and triggers portfolio recalculation.

**Interface**:

```python
class PriceEventConsumer:
    """Consumes price updates and triggers portfolio updates."""

    def __init__(
        self,
        performance_calculator: PerformanceCalculator,
        websocket_manager: WebSocketManager,
        bootstrap_servers: str
    ):
        self.calculator = performance_calculator
        self.websocket = websocket_manager
        self.consumer = KafkaConsumer(
            'market-data.prices.*',
            bootstrap_servers=bootstrap_servers,
            group_id='portfolio-updater',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

    async def start(self):
        """
        Start consuming price events.

        Flow:
        1. Receive price update from Kafka
        2. Find portfolios containing this ticker
        3. Recalculate portfolio performance
        4. Broadcast update via WebSocket
        """
        for message in self.consumer:
            price_data = message.value
            ticker = price_data['ticker']

            # Find affected portfolios
            portfolios = self.db.query(Portfolio).join(Holding).filter(
                Holding.ticker == ticker
            ).distinct().all()

            for portfolio in portfolios:
                # Recalculate performance
                performance = await self.calculator.calculate_portfolio_performance(
                    portfolio.id
                )

                # Broadcast to WebSocket subscribers
                await self.websocket.broadcast_to_topic(
                    f"portfolio.{portfolio.id}",
                    {
                        "type": "portfolio.update",
                        "data": performance.dict()
                    }
                )
```

**Consumer Group**: `portfolio-updater`
**Topics**: `market-data.prices.*` (wildcard subscription)

**Testing**: `backend/tests/test_price_event_consumer.py`

---

## Inter-Domain Communication

### Market Data → Portfolio

```
Price Update (Kafka) → PriceEventConsumer → PerformanceCalculator → WebSocket
```

1. **Trigger**: Price publisher emits new price to Kafka
2. **Consumer**: Portfolio price event consumer receives update
3. **Processing**: Performance calculator recalculates affected portfolios
4. **Notification**: WebSocket broadcasts updates to subscribed clients

---

## Caching Strategy

### Market Data Domain

| Data Type | Cache Key | TTL | Rationale |
|-----------|-----------|-----|-----------|
| Latest Price | `price:latest:{ticker}` | 30s | High frequency updates |
| Historical Prices | `price:history:{ticker}:{start}:{end}` | 1h | Historical data rarely changes |
| Fundamentals | `fundamentals:{ticker}` | 24h | Updated daily |

### Portfolio Domain

| Data Type | Cache Key | TTL | Rationale |
|-----------|-----------|-----|-----------|
| Portfolio Holdings | `portfolio:{id}:holdings` | 5min | Changes on user action |
| Portfolio Performance | `portfolio:{id}:performance` | 1min | Recalculated frequently |
| User Portfolios | `portfolios:user:{user_id}` | 5min | List rarely changes |

**Cache Invalidation**: Explicit invalidation on mutations (create, update, delete).

---

## Error Handling

### Custom Exceptions

```python
# Market Data Domain
class MarketDataError(Exception):
    """Base exception for market data errors."""
    pass

class TickerNotFoundError(MarketDataError):
    """Ticker does not exist."""
    pass

class PricingAPIError(MarketDataError):
    """External pricing API error."""
    pass

class RateLimitError(MarketDataError):
    """API rate limit exceeded."""
    pass

# Portfolio Domain
class PortfolioError(Exception):
    """Base exception for portfolio errors."""
    pass

class PortfolioNotFoundError(PortfolioError):
    """Portfolio does not exist."""
    pass

class HoldingNotFoundError(PortfolioError):
    """Holding does not exist."""
    pass

class InsufficientQuantityError(PortfolioError):
    """Attempting to sell more shares than owned."""
    pass
```

---

## Testing Strategy

### Unit Tests

- **Models**: Validation, business rules, computed properties
- **Services**: Business logic, error handling, cache behavior
- **Adapters**: API integration, error mapping, retry logic

### Integration Tests

- **Database**: CRUD operations, transactions, constraints
- **Kafka**: Message production/consumption, serialization
- **Cache**: Redis operations, invalidation, expiration

### Test Coverage Target

- Domain Services: 90%+
- Models: 95%+
- Adapters: 80%+ (external dependencies mocked)

---

## Future Enhancements

### Market Data Domain
- [ ] Real-time streaming price updates (WebSocket to external API)
- [ ] Options pricing and Greeks calculation
- [ ] Cryptocurrency support
- [ ] News and sentiment analysis integration
- [ ] Technical indicators (RSI, MACD, Bollinger Bands)

### Portfolio Domain
- [ ] Tax lot tracking (FIFO, LIFO, specific ID)
- [ ] Dividend tracking and reinvestment
- [ ] Asset allocation rebalancing recommendations
- [ ] Risk metrics (beta, Sharpe ratio, max drawdown)
- [ ] Currency conversion for international holdings
- [ ] Cost basis adjustments (splits, mergers)
- [ ] Trade execution planning (limit orders, stop losses)
