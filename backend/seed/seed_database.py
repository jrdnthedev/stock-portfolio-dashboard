"""
Database-enabled seed script for stock portfolio dashboard.
Uses SQLAlchemy to persist data to a real database.

Creates:
- 20 tickers with company information
- 5 years of historical OHLCV price data for each ticker
- 1 sample portfolio with 10 holdings
"""

import random
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

try:
    from backend.database import Holding, Portfolio, PricePoint, SessionLocal, Ticker, create_tables
except ImportError:
    from database import Holding, Portfolio, PricePoint, SessionLocal, Ticker, create_tables

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


def generate_mock_prices(
    start_price: float,
    start_date: datetime,
    days: int,
    volatility: float = 0.02,
) -> list[dict]:
    """
    Generate realistic mock price data using a random walk.

    Args:
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
                "date": current_date.date(),
                "open_price": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
            }
        )

        current_date += timedelta(days=1)

    return prices


def seed_database_real(db: Session) -> None:
    """
    Seed the database with sample data.

    Args:
        db: SQLAlchemy database session
    """
    print("Starting database seed...")

    # Step 1: Create 20 tickers
    print("\n1. Creating 20 tickers...")
    tickers = []
    for symbol, company_name, sector in TICKER_DATA:
        ticker = Ticker(
            symbol=symbol,
            company_name=company_name,
            exchange="NASDAQ" if sector == "Technology" else "NYSE",
            sector=sector,
            asset_class="Equity",
        )
        db.add(ticker)
        tickers.append(ticker)
        print(f"   ✓ Created {symbol} ({company_name})")

    db.commit()  # Commit to get IDs

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

    for i, ticker in enumerate(tickers):
        base_price = base_prices[i]

        price_data = generate_mock_prices(
            start_price=base_price,
            start_date=start_date,
            days=trading_days,
            volatility=0.015 if ticker.symbol in ["JNJ", "PG", "WMT"] else 0.025,
        )

        # Batch insert prices
        price_objects = [PricePoint(ticker_id=ticker.id, **price) for price in price_data]
        db.add_all(price_objects)

        latest_price = price_data[-1]["close"] if price_data else 0
        print(
            f"   ✓ Generated {len(price_data)} price points for {ticker.symbol} "
            f"(latest: ${latest_price:.2f})"
        )

    db.commit()

    # Step 3: Create sample portfolio with 10 holdings
    print("\n3. Creating sample portfolio with 10 holdings...")
    portfolio = Portfolio(
        name="Diversified Growth Portfolio",
        owner="demo_user",
        currency="USD",
        created_at=datetime.now(UTC),
    )
    db.add(portfolio)
    db.commit()  # Commit to get portfolio ID

    print("   ✓ Created portfolio: Diversified Growth Portfolio")

    # Select 10 random tickers for holdings
    selected_tickers = random.sample(tickers, 10)

    total_invested = 0.0
    for ticker in selected_tickers:
        # Get prices for this ticker (from ~1 year ago for cost basis)
        prices = (
            db.query(PricePoint)
            .filter(PricePoint.ticker_id == ticker.id)
            .order_by(PricePoint.date)
            .all()
        )

        year_ago_index = max(0, len(prices) - 252)  # ~1 year of trading days
        cost_basis_price = prices[year_ago_index].close if prices else 100.0

        # Random quantity between 10 and 200 shares
        quantity = random.uniform(10, 200)

        holding = Holding(
            portfolio_id=portfolio.id,
            ticker_id=ticker.id,
            quantity=round(quantity, 2),
            avg_cost_basis=round(cost_basis_price, 2),
            opened_at=datetime.now(UTC),
        )
        db.add(holding)

        invested = quantity * cost_basis_price
        total_invested += invested

        current_price = prices[-1].close if prices else cost_basis_price
        current_value = quantity * current_price
        gain_loss = current_value - invested
        gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else 0

        print(
            f"   ✓ {ticker.symbol}: {quantity:.2f} shares @ ${cost_basis_price:.2f} "
            f"(current: ${current_price:.2f}, P&L: {gain_loss_pct:+.2f}%)"
        )

    db.commit()
    print(f"\n   Total invested: ${total_invested:,.2f}")

    # Summary
    print("\n" + "=" * 70)
    print("Seed Summary:")
    print(f"  • {len(tickers)} tickers created")
    print(f"  • {trading_days} days of price data per ticker")
    print(f"  • {len(tickers) * trading_days:,} total price points")
    print("  • 1 portfolio created")
    print("  • 10 holdings created")
    print("=" * 70)


if __name__ == "__main__":
    # Create tables if they don't exist
    print("Creating database tables...")
    create_tables()

    # Create session and run seed
    db = SessionLocal()
    try:
        seed_database_real(db)
        print("\n✅ Database seeding completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()
