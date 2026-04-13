"""Pytest configuration for integration tests with testcontainers."""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from backend.database.database import get_db
from backend.database.models import Base


@asynccontextmanager
async def test_lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    No-op lifespan for integration tests.
    Integration tests don't need Kafka/Redis background services.
    """
    yield


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """
    Create and start a PostgreSQL container for the test session.
    The container persists for all tests in the session.
    """
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def test_engine(postgres_container: PostgresContainer):
    """
    Create a SQLAlchemy engine connected to the test database.
    """
    connection_url = postgres_container.get_connection_url()
    engine = create_engine(connection_url, echo=False)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup: drop all tables after tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create a new database session for each test function.
    Rolls back changes after each test to ensure isolation.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def seeded_db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create a new database session with seeded test data.
    Use this fixture for unit tests that need pre-populated data.
    Integration tests should use db_session and manage their own data.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()

    # Seed the database with test data
    from backend.seed.seed_database import seed_database_real

    seed_database_real(session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def seeded_client(seeded_db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with seeded database for unit tests.
    Use this fixture for unit tests that need pre-populated data.
    """
    from fastapi import APIRouter
    from fastapi.middleware.cors import CORSMiddleware

    from backend.middleware.auth import get_current_active_user, get_current_user
    from backend.middleware.logging import RequestLoggingMiddleware
    from backend.routes_market import router as market_router_v1
    from backend.routes_portfolio import router as portfolio_router_v1

    # Create test app without background services
    test_app = FastAPI(
        title="Stock Portfolio API - Test",
        description="Test instance without background services",
        version="1.0.0-test",
        lifespan=test_lifespan,  # Use no-op lifespan
    )

    # Configure middlewares
    test_app.add_middleware(RequestLoggingMiddleware)
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include versioned API router (v1)
    # For tests, we use /v1 prefix instead of /api/v1 to keep test URLs simpler
    api_v1_router = APIRouter(prefix="/v1")

    api_v1_router.include_router(market_router_v1, tags=["v1-market"])
    api_v1_router.include_router(portfolio_router_v1, tags=["v1-portfolio"])

    test_app.include_router(api_v1_router)

    # Add root and health endpoints for test compatibility
    from fastapi import status
    from fastapi.responses import JSONResponse

    import backend.gateway.health
    from backend.api.versioning import get_api_version, get_available_versions
    from backend.gateway.formatter import error_response, success_response

    @test_app.get("/")
    async def root() -> dict[str, str | list[str]]:
        """Root endpoint with API information and available versions."""
        return {
            "message": "Stock Portfolio API",
            "status": "running",
            "version": get_api_version(),
            "available_versions": get_available_versions(),
            "documentation": "/docs",
        }

    @test_app.get("/api/health")
    async def health_check() -> JSONResponse:
        """
        Comprehensive health check endpoint.

        Checks connectivity and status of:
        - PostgreSQL database
        - Redis cache
        - Kafka message broker

        Returns 200 if all services healthy, 503 if any service is down.
        """
        # Call through module reference to allow test patching
        health_data = backend.gateway.health.get_health_status()

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

    def override_get_db():
        try:
            yield seeded_db_session
        finally:
            pass

    # Mock authentication to return a test user
    async def override_get_current_user():
        return {"sub": "test_user", "role": "user", "disabled": False}

    async def override_get_current_active_user():
        return {"sub": "test_user", "role": "user", "disabled": False}

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(test_app) as test_client:
        yield test_client

    test_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with database dependency override.
    Each test gets a fresh client with an isolated database session.
    Uses a test-specific app without Kafka/Redis background services.
    For integration tests that manage their own test data.
    """
    from fastapi import APIRouter
    from fastapi.middleware.cors import CORSMiddleware

    from backend.middleware.auth import get_current_active_user, get_current_user
    from backend.middleware.logging import RequestLoggingMiddleware
    from backend.routes_market import router as market_router_v1
    from backend.routes_portfolio import router as portfolio_router_v1

    # Create test app without background services
    test_app = FastAPI(
        title="Stock Portfolio API - Test",
        description="Test instance without background services",
        version="1.0.0-test",
        lifespan=test_lifespan,  # Use no-op lifespan
    )

    # Configure middlewares
    test_app.add_middleware(RequestLoggingMiddleware)
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include versioned API router (v1)
    # For tests, we use /v1 prefix instead of /api/v1 to keep test URLs simpler
    api_v1_router = APIRouter(prefix="/v1")

    api_v1_router.include_router(market_router_v1, tags=["v1-market"])
    api_v1_router.include_router(portfolio_router_v1, tags=["v1-portfolio"])

    test_app.include_router(api_v1_router)

    # Add root and health endpoints for test compatibility
    from fastapi import status
    from fastapi.responses import JSONResponse

    import backend.gateway.health
    from backend.api.versioning import get_api_version, get_available_versions
    from backend.gateway.formatter import error_response, success_response

    @test_app.get("/")
    async def root() -> dict[str, str | list[str]]:
        """Root endpoint with API information and available versions."""
        return {
            "message": "Stock Portfolio API",
            "status": "running",
            "version": get_api_version(),
            "available_versions": get_available_versions(),
            "documentation": "/docs",
        }

    @test_app.get("/api/health")
    async def health_check() -> JSONResponse:
        """
        Comprehensive health check endpoint.

        Checks connectivity and status of:
        - PostgreSQL database
        - Redis cache
        - Kafka message broker

        Returns 200 if all services healthy, 503 if any service is down.
        """
        # Call through module reference to allow test patching
        health_data = backend.gateway.health.get_health_status()

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

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Mock authentication to return a test user
    async def override_get_current_user():
        return {"sub": "test_user", "role": "user", "disabled": False}

    async def override_get_current_active_user():
        return {"sub": "test_user", "role": "user", "disabled": False}

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(test_app) as test_client:
        yield test_client

    test_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def disable_cache(monkeypatch):
    """
    Disable Redis cache for integration tests.
    Override cache service to prevent external dependencies.
    """
    from backend.gateway.cache import CacheService

    # Mock cache service methods
    def mock_get(*_args, **_kwargs):
        return None

    def mock_set(*_args, **_kwargs):
        return True

    def mock_delete(*_args, **_kwargs):
        return True

    monkeypatch.setattr(CacheService, "get", mock_get)
    monkeypatch.setattr(CacheService, "set", mock_set)
    monkeypatch.setattr(CacheService, "delete", mock_delete)
