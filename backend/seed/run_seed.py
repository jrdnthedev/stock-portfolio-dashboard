"""
Seed runner that integrates seed data with portfolio services.
"""

from seed.seed_data import seed_database


def integrate_with_services() -> None:
    """
    Run the seed and show how to integrate with portfolio services.
    """
    # Generate seed data
    tickers, prices, portfolios = seed_database()

    print("\n" + "=" * 70)
    print("Integration Example:")
    print("=" * 70)

    # Show how to access the data
    print("\n📊 Available Tickers:")
    for _, ticker in list(tickers.tickers.items())[:5]:
        print(f"   {ticker['symbol']:<10} {ticker['company_name']:<40} {ticker['sector']}")
    print(f"   ... and {len(tickers.tickers) - 5} more")

    print("\n💰 Portfolio Holdings:")
    for portfolio_id, portfolio in portfolios.portfolios.items():
        print(f"\n   Portfolio: {portfolio['name']}")
        print(f"   Owner: {portfolio['owner']}")
        print(f"   Currency: {portfolio['currency']}")

        holdings = portfolios.get_portfolio_holdings(portfolio_id)
        print(f"\n   Holdings ({len(holdings)}):")

        for holding in holdings:
            holding_ticker: dict | None = tickers.get_ticker(holding["ticker_id"])
            symbol = holding_ticker["symbol"] if holding_ticker else "UNKNOWN"
            latest_price = prices.get_latest_price(holding["ticker_id"])
            current_price = latest_price["close"] if latest_price else 0

            market_value = holding["quantity"] * current_price
            cost_basis = holding["quantity"] * holding["avg_cost_basis"]
            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

            print(
                f"      {symbol:<8} {holding['quantity']:>8.2f} shares @ ${holding['avg_cost_basis']:>8.2f}  "
                f"Value: ${market_value:>10.2f}  P&L: ${pnl:>10.2f} ({pnl_pct:>+6.2f}%)"
            )

    print("\n💡 To use this data with PortfolioService, PerformanceCalculator, etc.,")
    print("   you can extend these storage classes or populate a real database.")


if __name__ == "__main__":
    integrate_with_services()
