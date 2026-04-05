# Seed Data

This directory contains scripts to populate the database with sample data for development and testing.

## Overview

The seed scripts create:
- **20 tickers** with realistic company information across different sectors
- **5 years of historical price data** (~1,260 trading days per ticker)
- **1 sample portfolio** with 10 diversified holdings

## Usage

### Run the seed script

```bash
cd backend
python -m seed.seed_data
```

### Run with service integration

```bash
python -m seed.run_seed
```

## Generated Data

### Tickers (20 total)

The seed includes major companies across different sectors:

**Technology:**
- AAPL (Apple Inc.)
- MSFT (Microsoft Corporation)
- GOOGL (Alphabet Inc.)
- NVDA (NVIDIA Corporation)
- META (Meta Platforms Inc.)

**Financial Services:**
- BRK.B (Berkshire Hathaway Inc.)
- JPM (JPMorgan Chase & Co.)
- V (Visa Inc.)
- MA (Mastercard Inc.)
- BAC (Bank of America Corp.)

**Healthcare:**
- JNJ (Johnson & Johnson)
- UNH (UnitedHealth Group Inc.)
- ABBV (AbbVie Inc.)
- PFE (Pfizer Inc.)

**Consumer:**
- AMZN (Amazon.com Inc.)
- TSLA (Tesla Inc.)
- WMT (Walmart Inc.)
- PG (Procter & Gamble Co.)
- HD (The Home Depot Inc.)

**Communication:**
- DIS (The Walt Disney Company)

### Price Data

- **Duration:** 5 years of historical data
- **Trading Days:** ~1,260 per ticker (252 days/year × 5 years)
- **Total Data Points:** ~25,200 price records
- **Generation Method:** Random walk with realistic volatility
  - Low volatility (1.5%): Defensive stocks (JNJ, PG, WMT)
  - Normal volatility (2.5%): Growth and tech stocks
- **OHLCV Data:** Open, High, Low, Close, Volume for each trading day
- **Weekends:** Automatically skipped (no trading on Sat/Sun)

### Sample Portfolio

**Name:** Diversified Growth Portfolio
**Owner:** demo_user
**Currency:** USD
**Holdings:** 10 positions randomly selected from the 20 tickers

Each holding includes:
- **Quantity:** Random amount between 10-200 shares
- **Cost Basis:** Price from ~1 year ago
- **Current Value:** Based on latest price
- **P&L:** Calculated gain/loss percentage

## Data Structure

The seed uses in-memory storage classes that mimic database operations:

### TickerData
- Stores ticker information (symbol, company name, sector, exchange)
- Provides lookup by UUID or symbol

### PriceData
- Stores OHLCV price points for each ticker
- Sorted by date for easy time-series analysis

### PortfolioData
- Stores portfolios and holdings
- Links holdings to tickers via UUID

## Integration

To integrate with your services:

```python
from seed.seed_data import seed_database

# Generate data
tickers, prices, portfolios = seed_database()

# Access ticker data
ticker = tickers.get_ticker_by_symbol("AAPL")

# Get price history
price_history = prices.get_prices(ticker_id)

# Get latest price
latest = prices.get_latest_price(ticker_id)

# Get portfolio holdings
holdings = portfolios.get_portfolio_holdings(portfolio_id)
```

## Extending the Seed

To add more data:

1. **Add Tickers:** Update the `TICKER_DATA` list in `seed_data.py`
2. **Adjust Time Range:** Modify the `start_date` calculation
3. **Create More Portfolios:** Call `portfolio_storage.create_portfolio()` multiple times
4. **Custom Holdings:** Add specific holdings with custom quantities

## Notes

- Prices use a random walk algorithm with realistic volatility
- Weekends are automatically excluded from trading days
- All IDs use UUIDs for consistency with the domain models
- The seed is idempotent and can be run multiple times (creates new UUIDs each time)
