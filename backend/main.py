import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import date

import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from backend.config import settings
    from backend.domains.market_data.service.price_publisher import PricePublisher
    from backend.gateway.formatter import error_response, success_response
    from backend.gateway.health import get_health_status
    from backend.middleware.logging import RequestLoggingMiddleware
    from backend.routes_market import router as market_router
    from backend.routes_portfolio import router as portfolio_router
except ImportError:
    from config import settings
    from domains.market_data.service.price_publisher import PricePublisher
    from gateway.formatter import error_response, success_response
    from gateway.health import get_health_status
    from middleware.logging import RequestLoggingMiddleware
    from routes_market import router as market_router
    from routes_portfolio import router as portfolio_router

logger = logging.getLogger(__name__)

# Global price publisher instance
price_publisher: PricePublisher | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler - starts/stops background services."""
    global price_publisher

    # Startup: Initialize and start PricePublisher
    logger.info("Starting PricePublisher...")
    kafka_servers = settings.kafka_bootstrap_servers.split(",")
    price_publisher = PricePublisher(
        kafka_bootstrap_servers=kafka_servers,
        topic="market.prices.live",
        interval_sec=5.0,
    )

    # Start publishing for ticker IDs 1-20 (adjust based on your seed data)
    # Using integers as ticker IDs for mock data
    ticker_ids = list(range(1, 21))
    start_date = date.today().strftime("%Y-%m-%d")
    price_publisher.start(ticker_ids, start_date)
    logger.info(f"PricePublisher started for {len(ticker_ids)} tickers")

    yield

    # Shutdown: Stop PricePublisher
    logger.info("Stopping PricePublisher...")
    if price_publisher:
        price_publisher.stop()
        logger.info("PricePublisher stopped")


app = FastAPI(
    title="Stock Portfolio API",
    description="Backend API for Stock Portfolio Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure request logging
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(market_router)
app.include_router(portfolio_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Stock Portfolio API", "status": "running"}


@app.get("/api/health")
async def health_check() -> JSONResponse:
    """
    Comprehensive health check endpoint.

    Checks connectivity and status of:
    - PostgreSQL database
    - Redis cache
    - Kafka message broker

    Returns 200 if all services healthy, 503 if any service is down.
    """
    health_data = get_health_status()

    if health_data["status"] == "healthy":
        response = success_response(
            data=health_data["services"],
            message="All services healthy",
            metadata={"timestamp": health_data["timestamp"]},
        )
        return JSONResponse(content=response, status_code=status.HTTP_200_OK)
    else:
        response = error_response(
            message="One or more services unhealthy",
            metadata={
                "timestamp": health_data["timestamp"],
                "services": health_data["services"],
            },
        )
        return JSONResponse(content=response, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


if __name__ == "__main__":
    # Run without reload to avoid import path issues with multiprocessing
    # For development with auto-reload, use command: uvicorn main:app --reload
    import sys

    # Ensure current directory is in Python path
    if "." not in sys.path:
        sys.path.insert(0, ".")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
