"""
Seed script for stock portfolio dashboard.
Creates:
- 20 tickers with company information
- 5 years of historical OHLCV price data for each ticker
- 1 sample portfolio with 10 holdings
"""

import random
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

# Ticker data: symbol, company name, sector
TICKER_DATA = [
    ("AAPL", "Apple Inc.", "Technology"),
    ("MSFT", "Microsoft Corporation", "Technology"),
    ("GOOGL", "Alphabet Inc.", "Technology"),
    ("AMZN", "Amazon.com Inc.", "Consumer Cyclical"),
    ("NVDA", "NVIDIA Corporation", "Technology"),
    ("META", "Meta Platforms Inc.", "Technology"),
    ("TSLA", "Tesla Inc.", "Consumer Cyclical"),
    ("BRK.B", "Berkshire Hathaway Inc.", "Financial Services"),
    ("JPM", "JPMorgan Chase & Co.", "Financial Services"),
    ("V", "Visa Inc.", "Financial Services"),
    ("JNJ", "Johnson & Johnson", "Healthcare"),
    ("WMT", "Walmart Inc.", "Consumer Defensive"),
    ("PG", "Procter & Gamble Co.", "Consumer Defensive"),
    ("MA", "Mastercard Inc.", "Financial Services"),
    ("UNH", "UnitedHealth Group Inc.", "Healthcare"),
    ("HD", "The Home Depot Inc.", "Consumer Cyclical"),
    ("DIS", "The Walt Disney Company", "Communication Services"),
    ("BAC", "Bank of America Corp.", "Financial Services"),
    ("ABBV", "AbbVie Inc.", "Healthcare"),
    ("PFE", "Pfizer Inc.", "Healthcare"),
]


class TickerData:
    """In-memory ticker storage"""

    def __init__(self) -> None:
        self.tickers: dict[UUID, dict] = {}
        self.symbol_to_id: dict[str, UUID] = {}

    def create_ticker(self, symbol: str, company_name: str, sector: str) -> UUID:
        ticker_id = uuid4()
        self.tickers[ticker_id] = {
            "id": ticker_id,
            "symbol": symbol,
            "company_name": company_name,
            "exchange": "NASDAQ" if sector == "Technology" else "NYSE",
            "sector": sector,
            "asset_class": "Equity",
        }
        self.symbol_to_id[symbol] = ticker_id
        return ticker_id

    def get_ticker(self, ticker_id: UUID) -> dict | None:
        return self.tickers.get(ticker_id)

    def get_ticker_by_symbol(self, symbol: str) -> dict | None:
        ticker_id = self.symbol_to_id.get(symbol)
        return self.tickers.get(ticker_id) if ticker_id else None


class PriceData:
    """In-memory price storage"""

    def __init__(self) -> None:
        self.prices: dict[UUID, list[dict]] = {}

    def create_price(
        self,
        ticker_id: UUID,
        date: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: int,
    ) -> None:
        if ticker_id not in self.prices:
            self.prices[ticker_id] = []

        self.prices[ticker_id].append(
            {
                "id": uuid4(),
                "ticker_id": ticker_id,
                "date": date.date(),
                "open_price": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )

    def get_prices(self, ticker_id: UUID) -> list[dict]:
        return sorted(self.prices.get(ticker_id, []), key=lambda p: p["date"])

    def get_latest_price(self, ticker_id: UUID) -> dict | None:
        prices = self.get_prices(ticker_id)
        return prices[-1] if prices else None


class PortfolioData:
    """In-memory portfolio storage"""

    def __init__(self) -> None:
        self.portfolios: dict[UUID, dict] = {}
        self.holdings: dict[UUID, dict] = {}

    def create_portfolio(self, name: str, owner: str, currency: str = "USD") -> UUID:
        portfolio_id = uuid4()
        self.portfolios[portfolio_id] = {
            "id": portfolio_id,
            "name": name,
            "owner": owner,
            "currency": currency,
            "created_at": datetime.now(UTC),
        }
        return portfolio_id

    def create_holding(
        self,
        portfolio_id: UUID,
        ticker_id: UUID,
        quantity: float,
        avg_cost_basis: float,
    ) -> UUID:
        holding_id = uuid4()
        self.holdings[holding_id] = {
            "id": holding_id,
            "portfolio_id": portfolio_id,
            "ticker_id": ticker_id,
            "quantity": quantity,
            "avg_cost_basis": avg_cost_basis,
            "opened_at": datetime.now(UTC),
        }
        return holding_id

    def get_portfolio_holdings(self, portfolio_id: UUID) -> list[dict]:
        return [h for h in self.holdings.values() if h["portfolio_id"] == portfolio_id]


def generate_mock_prices(
    ticker_id: UUID,
    start_price: float,
    start_date: datetime,
    days: int,
    volatility: float = 0.02,
) -> list[dict]:
    """
    Generate realistic mock price data using a random walk.

    Args:
        ticker_id: UUID of the ticker
        start_price: Starting price
        start_date: Starting date
        days: Number of days to generate
        volatility: Daily volatility (standard deviation)
    """
    prices = []
    current_price = start_price
    current_date = start_date

    for _ in range(days):
        # Skip weekends
        while current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            current_date += timedelta(days=1)

        # Random walk with drift
        daily_return = random.gauss(0.0005, volatility)  # Small positive drift
        current_price *= 1 + daily_return

        # Generate OHLCV
        open_price = current_price * random.uniform(0.99, 1.01)
        high = max(open_price, current_price) * random.uniform(1.0, 1.02)
        low = min(open_price, current_price) * random.uniform(0.98, 1.0)
        close = current_price
        volume = random.randint(1_000_000, 10_000_000)

        prices.append(
            {
                "ticker_id": ticker_id,
                "date": current_date,
                "open_price": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
            }
        )

        current_date += timedelta(days=1)

    return prices


def seed_database() -> tuple[TickerData, PriceData, PortfolioData]:
    """
    Main seed function that creates all the data.
    """
    print("Starting database seed...")

    ticker_storage = TickerData()
    price_storage = PriceData()
    portfolio_storage = PortfolioData()

    # Step 1: Create 20 tickers
    print("\n1. Creating 20 tickers...")
    ticker_ids = []
    for symbol, company_name, sector in TICKER_DATA:
        ticker_id = ticker_storage.create_ticker(symbol, company_name, sector)
        ticker_ids.append(ticker_id)
        print(f"   ✓ Created {symbol} ({company_name})")

    # Step 2: Generate 5 years of price data for each ticker
    print("\n2. Generating 5 years of price data for each ticker...")
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=5 * 365)  # 5 years
    trading_days = 5 * 252  # Approximate trading days in 5 years

    # Base prices for different tickers
    base_prices = [
        150,
        350,
        140,
        180,
        500,
        300,
        250,
        350,
        150,
        250,
        160,
        150,
        140,
        400,
        500,
        320,
        110,
        35,
        150,
        28,
    ]

    for i, ticker_id in enumerate(ticker_ids):
        ticker = ticker_storage.get_ticker(ticker_id)
        symbol = ticker["symbol"] if ticker else "UNKNOWN"
        base_price = base_prices[i]

        price_data = generate_mock_prices(
            ticker_id=ticker_id,
            start_price=base_price,
            start_date=start_date,
            days=trading_days,
            volatility=0.015 if symbol in ["JNJ", "PG", "WMT"] else 0.025,
        )

        for price in price_data:
            price_storage.create_price(**price)

        latest = price_storage.get_latest_price(ticker_id)
        latest_price = latest["close"] if latest else 0
        print(
            f"   ✓ Generated {len(price_data)} price points for {symbol} (latest: ${latest_price:.2f})"
        )

    # Step 3: Create sample portfolio with 10 holdings
    print("\n3. Creating sample portfolio with 10 holdings...")
    portfolio_id = portfolio_storage.create_portfolio(
        name="Diversified Growth Portfolio",
        owner="demo_user",
        currency="USD",
    )
    print("   ✓ Created portfolio: Diversified Growth Portfolio")

    # Select 10 random tickers for holdings
    selected_tickers = random.sample(ticker_ids, 10)

    total_invested = 0.0
    for ticker_id in selected_tickers:
        ticker = ticker_storage.get_ticker(ticker_id)
        symbol = ticker["symbol"] if ticker else "UNKNOWN"

        # Get a historical price (from ~1 year ago) as the cost basis
        all_prices = price_storage.get_prices(ticker_id)
        year_ago_index = max(0, len(all_prices) - 252)  # ~1 year of trading days
        cost_basis_price = all_prices[year_ago_index]["close"] if all_prices else 100.0

        # Random quantity between 10 and 200 shares
        quantity = random.uniform(10, 200)

        _ = portfolio_storage.create_holding(
            portfolio_id=portfolio_id,
            ticker_id=ticker_id,
            quantity=round(quantity, 2),
            avg_cost_basis=round(cost_basis_price, 2),
        )

        invested = quantity * cost_basis_price
        total_invested += invested

        latest = price_storage.get_latest_price(ticker_id)
        current_price = latest["close"] if latest else cost_basis_price
        current_value = quantity * current_price
        gain_loss = current_value - invested
        gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else 0

        print(
            f"   ✓ {symbol}: {quantity:.2f} shares @ ${cost_basis_price:.2f} "
            f"(current: ${current_price:.2f}, P&L: {gain_loss_pct:+.2f}%)"
        )

    print(f"\n   Total invested: ${total_invested:,.2f}")

    # Summary
    print("\n" + "=" * 70)
    print("Seed Summary:")
    print(f"  • {len(ticker_ids)} tickers created")
    print(f"  • {trading_days} days of price data per ticker")
    print(f"  • {len(ticker_ids) * trading_days:,} total price points")
    print("  • 1 portfolio created")
    print("  • 10 holdings created")
    print("=" * 70)

    return ticker_storage, price_storage, portfolio_storage


if __name__ == "__main__":
    # Run the seed
    tickers, prices, portfolios = seed_database()

    print("\n✅ Database seeding completed successfully!")
    print("\nYou can now use this data in your application.")
    print("To integrate with your services, import this module and use the storage objects.")
