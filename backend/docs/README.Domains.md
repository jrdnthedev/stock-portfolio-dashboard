# Domain Layer Documentation

> Business logic implementation using Domain-Driven Design (DDD) principles with Domain Events and Repository Pattern.

📚 **[Documentation Index](README.md)** | 🏠 **[Main README](../README.md)**

---

## Table of Contents
- [Overview](#overview)
- [Architecture Principles](#architecture-principles)
- [Market Data Domain](#market-data-domain)
- [Portfolio Domain](#portfolio-domain)
- [Event-Driven Architecture](#event-driven-architecture)
- [Repository Pattern](#repository-pattern)

---

## Overview

The domain layer implements business logic using **Domain-Driven Design** (DDD) principles. It consists of two primary domains: **Market Data** and **Portfolio Management**, each with their own models and services.

**Location**: `backend/domains/`

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

**Purpose**: Background service that generates mock price events and publishes to Kafka every 5 seconds.

**Implementation**:

```python
class PricePublisher:
    """Background service for publishing mock price updates."""

    def __init__(
        self,
        kafka_bootstrap_servers: list[str],
        topic: str,
        interval_sec: float = 5.0
    ):
        self.kafka_servers = kafka_bootstrap_servers
        self.topic = topic  # 'market.prices.live'
        self.interval_sec = interval_sec
        self.pricing_adapter = PricingAdapter(kafka_servers, topic)
        self.running = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self, ticker_ids: list[int], start_date: str) -> None:
        """
        Start background publishing loop.

        Flow:
        1. Spawn daemon thread
        2. Loop every interval_sec seconds
        3. Generate mock OHLCV for each ticker
        4. Publish PriceUpdated event to Kafka
        5. Continue until stop() called
        """
        if self.thread and self.thread.is_alive():
            logger.warning("PricePublisher already running")
            return

        self.running.set()
        self.thread = threading.Thread(
            target=self._publish_loop,
            args=(ticker_ids, start_date),
            daemon=True
        )
        self.thread.start()
        logger.info(f"PricePublisher started for {len(ticker_ids)} tickers")

    def _publish_loop(self, ticker_ids: list[int], start_date: str) -> None:
        """Background loop that publishes prices."""
        while self.running.is_set():
            for ticker_id in ticker_ids:
                self.pricing_adapter.generate_mock_ohlcv(
                    ticker_id=ticker_id,
                    start_date=start_date,
                    is_live=True  # Generate single data point
                )
            time.sleep(self.interval_sec)

    def stop(self) -> None:
        """Stop publishing and cleanup resources."""
        self.running.clear()
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("PricePublisher stopped")
```

**Integration**: Started in `main.py` lifespan handler for ticker IDs 1-20.

**Kafka Topic**: `market.prices.live`
**Message Format**:
```json
{
  "event": "PriceUpdated",
  "data": {
    "ticker_id": 1,
    "date": "2026-04-07",
    "open": 150.25,
    "high": 152.80,
    "low": 149.50,
    "close": 151.75,
    "volume": 1250000
  }
}
```

**Testing**: `backend/tests/test_price_publisher.py` and `backend/tests/test_pricing_adapter.py`

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

**Purpose**: CRUD operations for portfolios and holdings with Kafka event publishing.

**Key Methods**:

```python
class PortfolioService:
    """Manages portfolio operations with event publishing."""

    def __init__(
        self,
        kafka_bootstrap_servers: list[str],
        topic: str = "portfolio.holdings.changed"
    ):
        # Kafka producer for portfolio events
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = topic

    def add_holding(
        self,
        db: Session,
        portfolio_id: int,
        ticker_id: int,
        quantity: int,
        average_cost: float
    ) -> Holding:
        """
        Add a holding to a portfolio.

        Flow:
        1. Validate portfolio exists
        2. Create holding in database
        3. Publish HoldingAdded event to Kafka
        4. Return created holding
        """
        holding = Holding(
            portfolio_id=portfolio_id,
            ticker_id=ticker_id,
            quantity=quantity,
            average_cost=average_cost
        )
        db.add(holding)
        db.commit()
        db.refresh(holding)

        # Publish event
        self._publish_event({
            "event": "HoldingAdded",
            "portfolio_id": portfolio_id,
            "ticker_id": ticker_id,
            "quantity": quantity,
            "average_cost": average_cost
        })

        return holding

    def update_holding(
        self,
        db: Session,
        holding_id: int,
        quantity: int | None = None,
        average_cost: float | None = None
    ) -> Holding:
        """Update holding with event publishing."""
        # Update database and publish HoldingUpdated event
        pass

    def delete_holding(self, db: Session, holding_id: int) -> None:
        """Delete holding with event publishing."""
        # Delete from database and publish HoldingDeleted event
        pass

    def get_portfolios_by_ticker(self, ticker_id: int) -> list[int]:
        """
        Find all portfolio IDs that contain a specific ticker.

        Used by PortfolioPerformanceOrchestrator to determine
        which portfolios need recalculation when a price updates.
        """
        # Query database for portfolios with this ticker
        pass

    def get_holdings_for_calculation(
        self,
        portfolio_id: int
    ) -> list[tuple[int, Decimal, Decimal, str | None]]:
        """
        Get holdings formatted for PerformanceCalculator.

        Returns: List of (ticker_id, quantity, average_cost, sector)
        """
        # Query and format holdings data
        pass

    def _publish_event(self, event: dict) -> None:
        """Publish event to Kafka topic."""
        self.producer.send(self.topic, value=event)
        self.producer.flush()
```

**Kafka Integration**:
- **Topic**: `portfolio.holdings.changed`
- **Events**: `HoldingAdded`, `HoldingUpdated`, `HoldingDeleted`
- **Purpose**: Notify other services of portfolio changes

**Cache Invalidation**: Portfolio mutation methods invalidate relevant Redis caches.

**Testing**: `backend/tests/test_portfolio_service.py`

---

### 2. Performance Calculator

**Location**: `portfolio/services/performance_calculator.py`

**Purpose**: Calculates real-time portfolio and holding performance metrics without database dependencies.

**Implementation**:

```python
class PerformanceCalculator:
    """In-memory performance calculation engine."""

    def __init__(self):
        # In-memory price cache: {ticker_id: Decimal}
        self.prices: dict[int, Decimal] = {}

    def update_price(self, ticker_id: int, price: Decimal) -> None:
        """Update cached price for a ticker."""
        self.prices[ticker_id] = price
        logger.debug(f"Updated price for ticker {ticker_id}: {price}")

    def calculate_holding_performance(
        self,
        ticker_id: int,
        quantity: Decimal,
        average_cost: Decimal,
        total_portfolio_value: Decimal
    ) -> dict[str, Any]:
        """
        Calculate performance for a single holding.

        Returns:
        - market_value: quantity × current_price
        - unrealized_pnl: (current_price - average_cost) × quantity
        - unrealized_pnl_percent: (unrealized_pnl / cost_basis) × 100
        - weight: (market_value / total_portfolio_value) × 100
        """
        current_price = self.prices.get(ticker_id, Decimal('0'))
        cost_basis = quantity * average_cost
        market_value = quantity * current_price
        unrealized_pnl = market_value - cost_basis
        unrealized_pnl_percent = (
            (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else Decimal('0')
        )
        weight = (
            (market_value / total_portfolio_value * 100)
            if total_portfolio_value > 0
            else Decimal('0')
        )

        return {
            "ticker_id": ticker_id,
            "quantity": float(quantity),
            "average_cost": float(average_cost),
            "current_price": float(current_price),
            "market_value": float(market_value),
            "unrealized_pnl": float(unrealized_pnl),
            "unrealized_pnl_percent": float(unrealized_pnl_percent),
            "weight": float(weight),
        }

    def calculate_portfolio_performance(
        self,
        holdings: list[tuple[int, Decimal, Decimal, str | None]]  # (ticker_id, qty, avg_cost, sector)
    ) -> dict[str, Any]:
        """
        Calculate portfolio-level performance.

        Returns:
        - total_market_value: Sum of all holding market values
        - total_unrealized_pnl: Sum of all unrealized P&L
        - total_unrealized_pnl_percent: Overall portfolio return %
        - holdings: Array of holding performance metrics
        - sector_allocation: Breakdown by sector
        """
        # First pass: calculate total portfolio value
        total_value = sum(
            qty * self.prices.get(tid, Decimal('0'))
            for tid, qty, _, _ in holdings
        )

        # Second pass: calculate holding metrics with weights
        holding_performances = [
            self.calculate_holding_performance(tid, qty, avg_cost, total_value)
            for tid, qty, avg_cost, _ in holdings
        ]

        # Calculate totals
        total_cost = sum(float(h["quantity"]) * float(h["average_cost"]) for h in holding_performances)
        total_pnl = sum(float(h["unrealized_pnl"]) for h in holding_performances)
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

        # Sector allocation
        sector_allocation = self._calculate_sector_allocation(holdings, holding_performances)

        return {
            "total_market_value": float(total_value),
            "total_unrealized_pnl": total_pnl,
            "total_unrealized_pnl_percent": total_pnl_pct,
            "holdings": holding_performances,
            "sector_allocation": sector_allocation,
        }
```

**Key Features**:
- **In-memory price cache**: No database queries for price lookups
- **Real-time calculation**: Instant P&L updates when prices change
- **Sector allocation**: Automatic grouping by sector with weights
- **Percentage calculations**: Returns, weights, sector allocations

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

### 4. Price Event Consumer & Orchestrator

**Location**: `portfolio/services/price_event_consumer.py`

**Purpose**: Consumes price events from Kafka and orchestrates portfolio performance updates with WebSocket broadcasts.

**Components**:

#### PriceEventConsumer

```python
class PriceEventConsumer:
    """Kafka consumer for price update events."""

    def __init__(
        self,
        kafka_bootstrap_servers: list[str],
        topic: str,
        group_id: str = "portfolio-performance-group"
    ):
        self.consumer = KafkaConsumer(
            topic,  # 'market.prices.live'
            bootstrap_servers=kafka_bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )
        self.callback: Callable[[dict], None] | None = None
        self.running = threading.Event()
        self.thread: threading.Thread | None = None

    def set_callback(self, callback: Callable[[dict], None]) -> None:
        """Register callback function to handle price events."""
        self.callback = callback

    def start(self) -> None:
        """Start consuming events in background thread."""
        self.running.set()
        self.thread = threading.Thread(
            target=self._consume_loop,
            daemon=True
        )
        self.thread.start()

    def _consume_loop(self) -> None:
        """Background loop that processes Kafka messages."""
        for message in self.consumer:
            if not self.running.is_set():
                break

            event_data = message.value
            if self.callback:
                self.callback(event_data)

    def stop(self) -> None:
        """Stop consumer and cleanup."""
        self.running.clear()
        self.consumer.close()
```

#### PortfolioPerformanceOrchestrator

```python
class PortfolioPerformanceOrchestrator:
    """Coordinates price updates with portfolio recalculation and WebSocket broadcasts."""

    def __init__(
        self,
        portfolio_service: PortfolioService,
        performance_calculator: PerformanceCalculator,
        price_consumer: PriceEventConsumer,
        websocket_publisher: Callable[[str, dict], None] | None = None
    ):
        self.portfolio_service = portfolio_service
        self.calculator = performance_calculator
        self.consumer = price_consumer
        self.websocket_publisher = websocket_publisher

        # Register callback
        self.consumer.set_callback(self._on_price_updated)

    def start(self) -> None:
        """Start consuming price events."""
        self.consumer.start()
        logger.info("PortfolioPerformanceOrchestrator started")

    def stop(self) -> None:
        """Stop consuming events."""
        self.consumer.stop()
        logger.info("PortfolioPerformanceOrchestrator stopped")

    def _on_price_updated(self, event: dict) -> None:
        """
        Handle price update event.

        Flow:
        1. Extract ticker_id and price from event
        2. Update PerformanceCalculator price cache
        3. Query portfolios containing this ticker
        4. Recalculate performance for each portfolio
        5. Broadcast updates via WebSocket (if configured)
        """
        if event.get("event") != "PriceUpdated":
            return

        data = event.get("data", {})
        ticker_id = data.get("ticker_id")
        close_price = data.get("close")

        if not ticker_id or not close_price:
            return

        # Update price in calculator
        self.calculator.update_price(ticker_id, Decimal(str(close_price)))

        # Find affected portfolios
        portfolios_with_ticker = self.portfolio_service.get_portfolios_by_ticker(
            ticker_id
        )

        # Recalculate and broadcast
        for portfolio_id in portfolios_with_ticker:
            # Get updated holdings
            holdings = self.portfolio_service.get_holdings_for_calculation(
                portfolio_id
            )

            # Calculate performance
            performance = self.calculator.calculate_portfolio_performance(holdings)

            # Broadcast via WebSocket
            if self.websocket_publisher:
                self.websocket_publisher(
                    str(portfolio_id),
                    {
                        "event": "PortfolioPerformanceUpdated",
                        "portfolio_id": str(portfolio_id),
                        "data": performance,
                    }
                )
                logger.debug(f"Broadcast performance update for portfolio {portfolio_id}")
```

**Integration**: Started in `main.py` lifespan handler with WebSocketManager publisher.

**Event Flow**:
```
PricePublisher → Kafka (market.prices.live) → PriceEventConsumer →
Orchestrator._on_price_updated() → PerformanceCalculator →
WebSocketManager.broadcast_to_topic() → Connected Clients
```

**Testing**: `backend/tests/test_price_event_consumer.py` (14 tests)

---

## Inter-Domain Communication

### Event-Driven Architecture

The system uses **Kafka** for asynchronous communication between domains:

#### Kafka Topics

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `market.prices.live` | PricePublisher | PriceEventConsumer | Real-time price updates every 5 seconds |
| `portfolio.holdings.changed` | PortfolioService | (Future) | Portfolio mutation events |

#### Event Flow: Price Updates → Portfolio Recalculation

```
┌─────────────────┐
│ PricePublisher  │ (Background Service - 5s interval)
│  (Ticker 1-20)  │
└────────┬────────┘
         │
         │ publishes PriceUpdated events
         ▼
┌─────────────────────────┐
│  Kafka: market.prices.live │
└────────┬────────────────┘
         │
         │ consumed by
         ▼
┌─────────────────────────────────┐
│  PriceEventConsumer              │
│  (portfolio-performance-group)   │
└────────┬────────────────────────┘
         │
         │ triggers callback
         ▼
┌──────────────────────────────────────┐
│  PortfolioPerformanceOrchestrator    │
│  ._on_price_updated()                │
└────────┬─────────────────────────────┘
         │
         ├─→ PerformanceCalculator.update_price()
         │
         ├─→ PortfolioService.get_portfolios_by_ticker()
         │
         ├─→ PerformanceCalculator.calculate_portfolio_performance()
         │
         └─→ WebSocketManager.broadcast_to_topic()
              │
              ▼
         ┌─────────────────┐
         │ Connected Clients│
         │ (WebSocket /ws)  │
         └──────────────────┘
```

#### Message Formats

**PriceUpdated Event** (`market.prices.live`):
```json
{
  "event": "PriceUpdated",
  "data": {
    "ticker_id": 1,
    "date": "2026-04-07",
    "open": 150.25,
    "high": 152.80,
    "low": 149.50,
    "close": 151.75,
    "volume": 1250000
  }
}
```

**HoldingAdded Event** (`portfolio.holdings.changed`):
```json
{
  "event": "HoldingAdded",
  "portfolio_id": 1,
  "ticker_id": 5,
  "quantity": 100,
  "average_cost": 145.50
}
```

**PortfolioPerformanceUpdated** (WebSocket):
```json
{
  "event": "PortfolioPerformanceUpdated",
  "portfolio_id": "1",
  "data": {
    "total_market_value": 125000.00,
    "total_unrealized_pnl": 5000.00,
    "total_unrealized_pnl_percent": 4.17,
    "holdings": [...],
    "sector_allocation": {...}
  }
}
```

### Synchronous Communication

HTTP routes call domain services directly:

```
Routes (routes_portfolio.py)
  ↓
PortfolioService (database operations)
  ↓
Kafka Event Published
```

### Lifespan Management

Background services are managed by FastAPI lifespan handler in `main.py`:

**Startup**:
1. Initialize PricePublisher for tickers 1-20 with 5-second interval
2. Initialize PortfolioService with Kafka producer
3. Initialize PerformanceCalculator (in-memory price cache)
4. Initialize PriceEventConsumer (Kafka consumer)
5. Create WebSocket publisher function
6. Initialize PortfolioPerformanceOrchestrator with all dependencies
7. Start PricePublisher background thread
8. Start PriceEventConsumer background thread

**Shutdown**:
1. Stop PortfolioPerformanceOrchestrator (stops price consumer)
2. Stop PricePublisher (joins background thread)
3. Cleanup Kafka connections

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

### Unit Tests (270 tests)

**Scope**: Individual components tested in isolation with mocked dependencies.

**Coverage by Component**:
- **Gateway Layer**: cache.py, formatter.py, health.py, websocket_manager.py
- **Market Services**: pricing_adapter.py, price_publisher.py, market_data_service.py
- **Portfolio Services**: portfolio_service.py, performance_calculator.py, price_event_consumer.py
- **Routes**: routes_market.py, routes_portfolio.py, routes_websocket.py
- **Middleware**: logging.py
- **Utilities**: seed_data.py, seed_database.py

**Key Test Files**:
- `test_websocket_manager.py` (26 tests): Connection management, subscriptions, broadcasting
- `test_price_event_consumer.py` (14 tests): Kafka consumer, orchestrator, callbacks
- `test_performance_calculator.py`: P&L calculations, sector allocation
- `test_price_publisher.py`: Background publishing, lifecycle management
- `test_pricing_adapter.py`: Mock data generation, Kafka publishing
- `test_portfolio_service.py`: CRUD operations, Kafka event publishing
- `test_cache.py`: Redis operations, TTL, invalidation
- `test_formatter.py`: Response envelopes, error formatting
- `test_health.py`: PostgreSQL, Redis, Kafka health checks

### Integration Tests (45 tests)

**Scope**: Full HTTP request/response cycles with real PostgreSQL database.

**Test Files**:
- `integration_test_portfolio.py` (22 tests): Portfolio CRUD, holdings management, performance
- `integration_test_market.py` (23 tests): Price data, fundamentals, ticker filtering

**Infrastructure**:
- **Testcontainers**: PostgreSQL in Docker for isolated testing
- **No Kafka/Redis**: Integration tests focus on HTTP + database only
- **Automatic Skip**: Tests skip gracefully if Docker not available

### Test Execution

```bash
# All tests
pytest  # 315 tests

# Unit tests only (fast, no Docker required)
pytest tests/test_*.py  # 270 tests

# Integration tests only (requires Docker)
pytest tests/integration_test_*.py  # 45 tests

# Specific domain
pytest -k "websocket or price_event"  # WebSocket and Kafka consumer tests
pytest -k "portfolio"  # Portfolio-related tests
pytest -k "market"  # Market data tests

# With coverage
pytest --cov=backend --cov-report=html
```

---

## Future Enhancements

### Market Data Domain
- [ ] Real-time streaming from external APIs (WebSocket to Polygon.io/Alpha Vantage)
- [ ] Options pricing and Greeks calculation (implied volatility, delta, gamma)
- [ ] Cryptocurrency support (Bitcoin, Ethereum via Coinbase/Kraken APIs)
- [ ] News and sentiment analysis integration (NewsAPI, Twitter sentiment)
- [ ] Technical indicators library (RSI, MACD, Bollinger Bands, Moving Averages)
- [ ] Historical fundamental data tracking (quarterly earnings, balance sheets)
- [ ] Multiple data provider support with fallback logic

### Portfolio Domain
- [x] Real-time P&L calculation with price updates ✅
- [x] Event-driven portfolio recalculation via Kafka ✅
- [x] WebSocket broadcasting for live portfolio updates ✅
- [ ] Tax lot tracking (FIFO, LIFO, specific identification methods)
- [ ] Dividend tracking and automatic reinvestment (DRIP)
- [ ] Asset allocation rebalancing recommendations with threshold alerts
- [ ] Risk metrics calculation (portfolio beta, Sharpe ratio, max drawdown, VaR)
- [ ] Multi-currency support with real-time FX conversion
- [ ] Corporate action handling (stock splits, mergers, spin-offs)
- [ ] Trade execution planning (limit orders, stop losses, trailing stops)
- [ ] Performance attribution analysis (sector, security, allocation effects)
- [ ] Benchmark comparison (S&P 500, custom indices)
- [ ] Tax loss harvesting opportunities identification

### Event-Driven Architecture
- [x] Price event publishing (market.prices.live) ✅
- [x] Portfolio event publishing (portfolio.holdings.changed) ✅
- [x] Price event consumption with portfolio orchestration ✅
- [ ] Portfolio event consumers for audit logging
- [ ] Event replay capability for debugging
- [ ] Event sourcing for portfolio state reconstruction
- [ ] Dead letter queue handling for failed events
- [ ] Event schema validation and versioning

### WebSocket & Real-Time Features
- [x] Redis-backed WebSocket connection registry ✅
- [x] Topic-based subscriptions for portfolio updates ✅
- [x] Portfolio performance broadcasting ✅
- [ ] JWT authentication for WebSocket connections
- [ ] Portfolio-level authorization checks
- [ ] Market-wide update broadcasting (index movements)
- [ ] User-specific notification channels
- [ ] Connection heartbeat and auto-reconnection
- [ ] Message acknowledgment and guaranteed delivery
- [ ] Rate limiting per client

---

## See Also

- **[Cache Service](README.Cache.md)** - Caching strategies in domain services
- **[WebSocket Manager](README.WebSocket.md)** - Real-time event broadcasting
- **[Integration Testing](README.Integration.md)** - Testing domain services
- **[Authentication](README.Auth.md)** - Securing domain endpoints

---

**Last Updated**: April 2026
**Component**: Domain-Driven Design Implementation
**Module**: `backend/domains/`

