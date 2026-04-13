import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date

import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.api.versioning import (
    create_api_v1_router,
    create_websocket_router,
    get_api_version,
    get_available_versions,
)
from backend.config import settings
from backend.container import Container
from backend.database.database import SessionLocal
from backend.database.models import Ticker
from backend.domains.market_data.service.price_publisher import PricePublisher
from backend.domains.portfolio.services.alert_publisher import AlertPublisher
from backend.domains.portfolio.services.performance_calculator import PerformanceCalculator
from backend.domains.portfolio.services.portfolio_service import PortfolioService
from backend.domains.portfolio.services.price_event_consumer import (
    PortfolioPerformanceOrchestrator,
    PriceEventConsumer,
)
from backend.gateway.formatter import error_response, success_response
from backend.gateway.health import get_health_status
from backend.gateway.websocket_manager import create_portfolio_publisher
from backend.infrastructure.repositories.sqlalchemy_portfolio_repository import (
    SQLAlchemyHoldingRepository,
    SQLAlchemyPortfolioRepository,
)
from backend.middleware.logging import RequestLoggingMiddleware
from backend.middleware.versioning import APIVersionMiddleware

logger = logging.getLogger(__name__)


@dataclass
class AppState:
    """Application state container for background services."""

    price_publisher: PricePublisher | None
    portfolio_orchestrator: PortfolioPerformanceOrchestrator | None
    db_session: Session
    container: Container


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler - starts/stops background services."""
    # Initialize dependency injection container
    container = Container()

    kafka_servers = settings.kafka_bootstrap_servers.split(",")

    # Create database session for fetching tickers and initializing services
    db_session = SessionLocal()

    # Fetch all ticker UUIDs from the database for price publishing
    try:
        tickers = db_session.query(Ticker).all()
        ticker_ids = [ticker.id for ticker in tickers]
        logger.info(f"Fetched {len(ticker_ids)} tickers from database for price publishing")
    except Exception as e:
        logger.error(f"Failed to fetch tickers from database: {e}")
        ticker_ids = []

    # Startup: Initialize and start PricePublisher with real ticker UUIDs
    price_publisher: PricePublisher | None = None
    if ticker_ids:
        logger.info("Starting PricePublisher...")
        price_publisher = PricePublisher(
            kafka_bootstrap_servers=kafka_servers,
            topic="market.prices.live",
            interval_sec=5.0,
        )
        start_date = date.today().strftime("%Y-%m-%d")
        price_publisher.start(ticker_ids, start_date)
        logger.info(f"PricePublisher started for {len(ticker_ids)} tickers")
    else:
        logger.warning("No tickers found in database - PricePublisher not started")

    # Startup: Initialize and start PriceEventConsumer with PortfolioPerformanceOrchestrator
    logger.info("Starting PriceEventConsumer...")

    # Create repository instances
    portfolio_repo = SQLAlchemyPortfolioRepository(db_session)
    holding_repo = SQLAlchemyHoldingRepository(db_session)

    portfolio_service = PortfolioService(
        portfolio_repo=portfolio_repo,
        holding_repo=holding_repo,
        kafka_bootstrap_servers=kafka_servers,
        topic="portfolio.holdings.changed",
    )
    performance_calculator = PerformanceCalculator()

    # Initialize AlertPublisher for price movement alerts
    alert_publisher = AlertPublisher(
        kafka_bootstrap_servers=kafka_servers,
        topic="portfolio.alerts",
    )
    logger.info("AlertPublisher initialized for price movement alerts")

    price_consumer = PriceEventConsumer(
        kafka_bootstrap_servers=kafka_servers,
        topic="market.prices.live",
        group_id="portfolio-performance-group",
    )

    # Create WebSocket publisher for real-time portfolio updates
    websocket_publisher = create_portfolio_publisher()
    logger.info("WebSocket publisher created for portfolio updates")

    # Create orchestrator to coordinate price updates with performance calculations and alerts
    portfolio_orchestrator = PortfolioPerformanceOrchestrator(
        portfolio_service=portfolio_service,
        performance_calculator=performance_calculator,
        price_consumer=price_consumer,
        alert_publisher=alert_publisher,
        websocket_publisher=websocket_publisher,
    )

    # Start consuming price events
    portfolio_orchestrator.start()
    logger.info("PriceEventConsumer started - listening for price updates")

    # Store services in application state
    _app.state.services = AppState(
        price_publisher=price_publisher,
        portfolio_orchestrator=portfolio_orchestrator,
        db_session=db_session,
        container=container,
    )

    logger.info("Dependency injection container initialized")

    yield

    # Shutdown: Stop background services
    logger.info("Stopping background services...")

    if _app.state.services.portfolio_orchestrator:
        _app.state.services.portfolio_orchestrator.stop()
        logger.info("PriceEventConsumer stopped")

    if _app.state.services.price_publisher:
        _app.state.services.price_publisher.stop()
        logger.info("PricePublisher stopped")

    # Close database session
    _app.state.services.db_session.close()
    logger.info("Database session closed")


app = FastAPI(
    title="Stock Portfolio API",
    description="Backend API for Stock Portfolio Dashboard with versioning support",
    version=get_api_version(),
    lifespan=lifespan,
)

# Configure API versioning middleware
app.add_middleware(APIVersionMiddleware)

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

# Include versioned API routers
api_v1 = create_api_v1_router()
app.include_router(api_v1)

# Include WebSocket router (not versioned in URL path)
ws_router = create_websocket_router()
app.include_router(ws_router)


@app.get("/")
async def root() -> dict[str, str | list[str]]:
    """Root endpoint with API information and available versions."""
    return {
        "message": "Stock Portfolio API",
        "status": "running",
        "version": get_api_version(),
        "available_versions": get_available_versions(),
        "documentation": "/docs",
    }


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
