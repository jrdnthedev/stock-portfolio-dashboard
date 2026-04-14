"""Shared test fixtures and mock helpers for reducing code duplication.

This module contains reusable fixtures and helper classes that are commonly
used across multiple test files.
"""

import time
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, Mock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from domains.portfolio.models.models import Holding, Portfolio
from domains.portfolio.repositories.portfolio_repository import (
    HoldingRepository,
    PortfolioRepository,
)

# ==============================================================================
# Helper Functions for Creating Test Data
# ==============================================================================


def make_portfolio(**kwargs: Any) -> Portfolio:
    """Create a Portfolio instance with default values for testing.

    Args:
        **kwargs: Override default values for any Portfolio field.

    Returns:
        Portfolio instance with test data.
    """
    defaults: dict[str, Any] = {
        "id": uuid4(),
        "name": "Test Portfolio",
        "owner": "test_user",
        "currency": "USD",
        "created_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return Portfolio(**defaults)


def make_holding(**kwargs: Any) -> Holding:
    """Create a Holding instance with default values for testing.

    Args:
        **kwargs: Override default values for any Holding field.

    Returns:
        Holding instance with test data.
    """
    defaults: dict[str, Any] = {
        "id": uuid4(),
        "portfolio_id": uuid4(),
        "ticker_id": uuid4(),
        "quantity": 100.0,
        "avg_cost_basis": 50.0,
        "opened_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return Holding(**defaults)


# ==============================================================================
# Mock Kafka Producer
# ==============================================================================


@pytest.fixture
def mock_kafka_producer() -> Generator[MagicMock, None, None]:
    """Mock Kafka producer for testing message publishing.

    Patches KafkaProducer in common locations. For service-specific patches,
    override this fixture in your test file with the appropriate patch path.
    """
    from unittest.mock import patch

    # Patch common KafkaProducer import locations
    patches = [
        patch("kafka.KafkaProducer"),
        patch("domains.portfolio.services.alert_publisher.KafkaProducer"),
        patch("domains.portfolio.services.portfolio_service.KafkaProducer"),
    ]

    started_patches = [p.start() for p in patches]
    mock_instance = MagicMock()

    for mock in started_patches:
        mock.return_value = mock_instance

    yield mock_instance

    for p in patches:
        p.stop()


# ==============================================================================
# Mock Repository Pattern
# ==============================================================================


@pytest.fixture
def mock_portfolio_repo() -> Mock:
    """Mock PortfolioRepository with in-memory storage."""
    repo = Mock(spec=PortfolioRepository)
    storage: dict[UUID, Portfolio] = {}

    def create(portfolio: Portfolio) -> Portfolio:
        storage[portfolio.id] = portfolio
        return portfolio

    def get_by_id(portfolio_id: UUID) -> Portfolio | None:
        return storage.get(portfolio_id)

    def list_by_owner(owner: str) -> list[Portfolio]:
        return [p for p in storage.values() if p.owner == owner]

    def list_all() -> list[Portfolio]:
        return list(storage.values())

    def update(portfolio: Portfolio) -> Portfolio:
        if portfolio.id not in storage:
            raise ValueError(f"Portfolio {portfolio.id} not found")
        storage[portfolio.id] = portfolio
        return portfolio

    def delete(portfolio_id: UUID) -> bool:
        if portfolio_id in storage:
            del storage[portfolio_id]
            return True
        return False

    repo.create.side_effect = create
    repo.get_by_id.side_effect = get_by_id
    repo.list_by_owner.side_effect = list_by_owner
    repo.list_all.side_effect = list_all
    repo.update.side_effect = update
    repo.delete.side_effect = delete
    return repo


@pytest.fixture
def mock_holding_repo() -> Mock:
    """Mock HoldingRepository with in-memory storage."""
    repo = Mock(spec=HoldingRepository)
    storage: dict[UUID, Holding] = {}

    def create(holding: Holding) -> Holding:
        storage[holding.id] = holding
        return holding

    def get_by_id(holding_id: UUID) -> Holding | None:
        return storage.get(holding_id)

    def list_by_portfolio(portfolio_id: UUID) -> list[Holding]:
        return [h for h in storage.values() if h.portfolio_id == portfolio_id]

    def list_by_ticker(ticker_id: UUID) -> list[Holding]:
        return [h for h in storage.values() if h.ticker_id == ticker_id]

    def update(holding: Holding) -> Holding:
        if holding.id not in storage:
            raise ValueError(f"Holding {holding.id} not found")
        storage[holding.id] = holding
        return holding

    def delete(holding_id: UUID) -> bool:
        if holding_id in storage:
            del storage[holding_id]
            return True
        return False

    def delete_by_portfolio(portfolio_id: UUID) -> int:
        to_delete = [h_id for h_id, h in storage.items() if h.portfolio_id == portfolio_id]
        for h_id in to_delete:
            del storage[h_id]
        return len(to_delete)

    repo.create.side_effect = create
    repo.get_by_id.side_effect = get_by_id
    repo.list_by_portfolio.side_effect = list_by_portfolio
    repo.list_by_ticker.side_effect = list_by_ticker
    repo.update.side_effect = update
    repo.delete.side_effect = delete
    repo.delete_by_portfolio.side_effect = delete_by_portfolio
    return repo


# ==============================================================================
# Mock Cache Service
# ==============================================================================


@pytest.fixture
def mock_cache() -> MagicMock:
    """Mock cache service for testing caching behavior."""
    cache = MagicMock()
    cache.get.return_value = None
    cache.set.return_value = True
    cache.delete.return_value = True
    return cache


@pytest.fixture
def mock_redis() -> Generator[MagicMock, None, None]:
    """Mock Redis client for testing Redis-dependent code."""
    from unittest.mock import patch

    with patch("backend.gateway.cache.redis.Redis") as mock:
        redis_instance = MagicMock()
        mock.return_value = redis_instance
        redis_instance.ping.return_value = True
        yield redis_instance


# ==============================================================================
# Mock Database Session
# ==============================================================================


@pytest.fixture
def mock_db_session() -> Mock:
    """Create a mock database session."""
    session = Mock(spec=Session)
    session.add = Mock()
    session.add_all = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.query = Mock()
    return session


# ==============================================================================
# Mock Kafka Consumer
# ==============================================================================


class DummyKafkaConsumer:
    """Mock Kafka consumer for testing message consumption."""

    def __init__(
        self,
        *topics: str,
        bootstrap_servers: list[str] | None = None,
        group_id: str | None = None,
        value_deserializer: object = None,
        auto_offset_reset: str | None = None,
        enable_auto_commit: bool = True,
    ) -> None:
        _ = topics, bootstrap_servers, group_id, value_deserializer
        _ = auto_offset_reset, enable_auto_commit
        self.messages: list[Any] = []
        self._index = 0
        self.closed = False

    def __iter__(self) -> "DummyKafkaConsumer":
        return self

    def __next__(self) -> Any:
        if self._index >= len(self.messages):
            time.sleep(0.01)  # Prevent tight loop
            raise StopIteration
        msg = MagicMock()
        msg.value = self.messages[self._index]
        self._index += 1
        return msg

    def add_message(self, value: Any) -> None:
        """Add a message to be consumed."""
        self.messages.append(value)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def mock_kafka_consumer() -> DummyKafkaConsumer:
    """Mock Kafka consumer for testing."""
    return DummyKafkaConsumer()


# ==============================================================================
# Mock WebSocket
# ==============================================================================


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing."""
    from unittest.mock import AsyncMock

    from fastapi import WebSocket

    ws = AsyncMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws
