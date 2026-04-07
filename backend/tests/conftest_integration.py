"""Pytest configuration for integration tests with testcontainers."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from backend.database.database import get_db
from backend.database.models import Base
from backend.main import app


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
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with database dependency override.
    Each test gets a fresh client with an isolated database session.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


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
