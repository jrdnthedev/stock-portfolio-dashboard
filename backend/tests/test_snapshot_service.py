from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from domains.portfolio.services.snapshot_service import SnapshotService


@pytest.fixture
def service() -> SnapshotService:
    return SnapshotService()


class TestSnapshotServiceCreation:
    def test_create_snapshot(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()
        snapshot_date = date(2024, 1, 15)

        snapshot = service.create_snapshot(
            portfolio_id=portfolio_id,
            snapshot_date=snapshot_date,
            total_value=10000.0,
            daily_return=2.5,
            cumulative_return=15.0,
        )

        assert snapshot.portfolio_id == portfolio_id
        assert snapshot.date == snapshot_date
        assert snapshot.total_value == 10000.0
        assert snapshot.daily_return == 2.5
        assert snapshot.cumulative_return == 15.0
        assert portfolio_id in service.snapshots
        assert snapshot in service.snapshots[portfolio_id]

    def test_create_snapshot_defaults_returns_to_zero(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()
        snapshot = service.create_snapshot(
            portfolio_id=portfolio_id, snapshot_date=date(2024, 1, 15), total_value=10000.0
        )

        assert snapshot.daily_return == 0.0
        assert snapshot.cumulative_return == 0.0

    def test_create_snapshot_keeps_sorted_by_date(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()

        s3 = service.create_snapshot(portfolio_id, date(2024, 1, 17), 12000.0)
        s1 = service.create_snapshot(portfolio_id, date(2024, 1, 15), 10000.0)
        s2 = service.create_snapshot(portfolio_id, date(2024, 1, 16), 11000.0)

        snapshots = service.snapshots[portfolio_id]
        assert snapshots[0] == s1
        assert snapshots[1] == s2
        assert snapshots[2] == s3


class TestSnapshotServiceGenerateDailySnapshot:
    def test_generate_daily_snapshot_first_snapshot(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()
        snapshot = service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=10000.0,
            snapshot_date=date(2024, 1, 15),
        )

        assert snapshot.total_value == 10000.0
        assert snapshot.daily_return == 0.0
        assert snapshot.cumulative_return == 0.0

    def test_generate_daily_snapshot_calculates_daily_return(
        self, service: SnapshotService
    ) -> None:
        portfolio_id = uuid4()

        # First snapshot
        service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=10000.0,
            snapshot_date=date(2024, 1, 15),
        )

        # Second snapshot with 5% gain
        snapshot2 = service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=10500.0,
            snapshot_date=date(2024, 1, 16),
        )

        assert snapshot2.daily_return == 5.0
        assert snapshot2.cumulative_return == 5.0

    def test_generate_daily_snapshot_calculates_cumulative_return(
        self, service: SnapshotService
    ) -> None:
        portfolio_id = uuid4()

        # Day 1: $10,000
        service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=10000.0,
            snapshot_date=date(2024, 1, 15),
        )

        # Day 2: $10,500 (5% gain)
        service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=10500.0,
            snapshot_date=date(2024, 1, 16),
        )

        # Day 3: $11,025 (5% gain) but cumulative is 10.25% from day 1
        snapshot3 = service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=11025.0,
            snapshot_date=date(2024, 1, 17),
        )

        assert snapshot3.daily_return == 5.0
        assert snapshot3.cumulative_return == 10.25

    def test_generate_daily_snapshot_handles_negative_returns(
        self, service: SnapshotService
    ) -> None:
        portfolio_id = uuid4()

        service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=10000.0,
            snapshot_date=date(2024, 1, 15),
        )

        snapshot2 = service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=9500.0,
            snapshot_date=date(2024, 1, 16),
        )

        assert snapshot2.daily_return == -5.0
        assert snapshot2.cumulative_return == -5.0

    def test_generate_daily_snapshot_uses_today_if_no_date(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()
        today = datetime.now(UTC).date()

        snapshot = service.generate_daily_snapshot(
            portfolio_id=portfolio_id, current_total_value=10000.0
        )

        assert snapshot.date == today

    def test_generate_daily_snapshot_handles_zero_previous_value(
        self, service: SnapshotService
    ) -> None:
        portfolio_id = uuid4()

        service.create_snapshot(portfolio_id, date(2024, 1, 15), 0.0)

        snapshot2 = service.generate_daily_snapshot(
            portfolio_id=portfolio_id,
            current_total_value=10000.0,
            snapshot_date=date(2024, 1, 16),
        )

        # Should handle division by zero gracefully
        assert snapshot2.daily_return == 0.0


class TestSnapshotServiceRetrieval:
    def test_get_snapshots_all(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()

        s1 = service.create_snapshot(portfolio_id, date(2024, 1, 15), 10000.0)
        s2 = service.create_snapshot(portfolio_id, date(2024, 1, 16), 10500.0)
        s3 = service.create_snapshot(portfolio_id, date(2024, 1, 17), 11000.0)

        snapshots = service.get_snapshots(portfolio_id)
        assert len(snapshots) == 3
        assert s1 in snapshots
        assert s2 in snapshots
        assert s3 in snapshots

    def test_get_snapshots_with_start_date(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()

        s1 = service.create_snapshot(portfolio_id, date(2024, 1, 15), 10000.0)
        s2 = service.create_snapshot(portfolio_id, date(2024, 1, 16), 10500.0)
        s3 = service.create_snapshot(portfolio_id, date(2024, 1, 17), 11000.0)

        snapshots = service.get_snapshots(portfolio_id, start_date=date(2024, 1, 16))
        assert len(snapshots) == 2
        assert s1 not in snapshots
        assert s2 in snapshots
        assert s3 in snapshots

    def test_get_snapshots_with_end_date(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()

        s1 = service.create_snapshot(portfolio_id, date(2024, 1, 15), 10000.0)
        s2 = service.create_snapshot(portfolio_id, date(2024, 1, 16), 10500.0)
        s3 = service.create_snapshot(portfolio_id, date(2024, 1, 17), 11000.0)

        snapshots = service.get_snapshots(portfolio_id, end_date=date(2024, 1, 16))
        assert len(snapshots) == 2
        assert s1 in snapshots
        assert s2 in snapshots
        assert s3 not in snapshots

    def test_get_snapshots_with_date_range(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()

        s1 = service.create_snapshot(portfolio_id, date(2024, 1, 15), 10000.0)
        s2 = service.create_snapshot(portfolio_id, date(2024, 1, 16), 10500.0)
        s3 = service.create_snapshot(portfolio_id, date(2024, 1, 17), 11000.0)
        s4 = service.create_snapshot(portfolio_id, date(2024, 1, 18), 11500.0)

        snapshots = service.get_snapshots(
            portfolio_id, start_date=date(2024, 1, 16), end_date=date(2024, 1, 17)
        )
        assert len(snapshots) == 2
        assert s2 in snapshots
        assert s3 in snapshots
        assert s1 not in snapshots
        assert s4 not in snapshots

    def test_get_snapshots_empty_portfolio(self, service: SnapshotService) -> None:
        snapshots = service.get_snapshots(uuid4())
        assert snapshots == []

    def test_get_latest_snapshot(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()

        service.create_snapshot(portfolio_id, date(2024, 1, 15), 10000.0)
        service.create_snapshot(portfolio_id, date(2024, 1, 16), 10500.0)
        s3 = service.create_snapshot(portfolio_id, date(2024, 1, 17), 11000.0)

        latest = service.get_latest_snapshot(portfolio_id)
        assert latest == s3

    def test_get_latest_snapshot_returns_none_if_empty(self, service: SnapshotService) -> None:
        latest = service.get_latest_snapshot(uuid4())
        assert latest is None


class TestSnapshotServiceDeletion:
    def test_delete_snapshots(self, service: SnapshotService) -> None:
        portfolio_id = uuid4()

        service.create_snapshot(portfolio_id, date(2024, 1, 15), 10000.0)
        service.create_snapshot(portfolio_id, date(2024, 1, 16), 10500.0)

        result = service.delete_snapshots(portfolio_id)
        assert result is True
        assert portfolio_id not in service.snapshots

    def test_delete_snapshots_returns_false_if_not_found(self, service: SnapshotService) -> None:
        result = service.delete_snapshots(uuid4())
        assert result is False
