from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from ..models.models import PerformanceSnapshot


class SnapshotService:
    """
    Generates and stores daily performance snapshots for historical value charts.
    """

    def __init__(self) -> None:
        # In-memory storage: portfolio_id -> list of snapshots
        self.snapshots: dict[UUID, list[PerformanceSnapshot]] = {}

    def create_snapshot(
        self,
        portfolio_id: UUID,
        snapshot_date: date,
        total_value: float,
        daily_return: float = 0.0,
        cumulative_return: float = 0.0,
    ) -> PerformanceSnapshot:
        """
        Create a performance snapshot for a portfolio.

        Args:
            portfolio_id: UUID of the portfolio
            snapshot_date: Date of the snapshot
            total_value: Total market value of the portfolio at this date
            daily_return: Daily return percentage (calculated relative to previous day)
            cumulative_return: Cumulative return percentage since inception
        """
        snapshot = PerformanceSnapshot(
            id=uuid4(),
            portfolio_id=portfolio_id,
            date=snapshot_date,
            total_value=total_value,
            daily_return=daily_return,
            cumulative_return=cumulative_return,
        )

        if portfolio_id not in self.snapshots:
            self.snapshots[portfolio_id] = []

        self.snapshots[portfolio_id].append(snapshot)
        # Keep snapshots sorted by date
        self.snapshots[portfolio_id].sort(key=lambda s: s.date)

        return snapshot

    def generate_daily_snapshot(
        self,
        portfolio_id: UUID,
        current_total_value: float,
        snapshot_date: date | None = None,
    ) -> PerformanceSnapshot:
        """
        Generate a daily snapshot with calculated returns.

        Args:
            portfolio_id: UUID of the portfolio
            current_total_value: Current total market value
            snapshot_date: Date for the snapshot (defaults to today)
        """
        if snapshot_date is None:
            snapshot_date = datetime.now(UTC).date()

        # Get previous snapshots for this portfolio
        previous_snapshots = self.snapshots.get(portfolio_id, [])

        # Calculate daily return
        daily_return = 0.0
        if previous_snapshots:
            last_snapshot = previous_snapshots[-1]
            if last_snapshot.total_value != 0:
                daily_return = (
                    (current_total_value - last_snapshot.total_value)
                    / last_snapshot.total_value
                    * 100
                )

        # Calculate cumulative return (since first snapshot)
        cumulative_return = 0.0
        if previous_snapshots:
            first_snapshot = previous_snapshots[0]
            if first_snapshot.total_value != 0:
                cumulative_return = (
                    (current_total_value - first_snapshot.total_value)
                    / first_snapshot.total_value
                    * 100
                )

        return self.create_snapshot(
            portfolio_id=portfolio_id,
            snapshot_date=snapshot_date,
            total_value=current_total_value,
            daily_return=daily_return,
            cumulative_return=cumulative_return,
        )

    def get_snapshots(
        self,
        portfolio_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[PerformanceSnapshot]:
        """
        Retrieve performance snapshots for a portfolio within a date range.

        Args:
            portfolio_id: UUID of the portfolio
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)
        """
        snapshots = self.snapshots.get(portfolio_id, [])

        if start_date:
            snapshots = [s for s in snapshots if s.date >= start_date]
        if end_date:
            snapshots = [s for s in snapshots if s.date <= end_date]

        return snapshots

    def get_latest_snapshot(self, portfolio_id: UUID) -> PerformanceSnapshot | None:
        """Get the most recent snapshot for a portfolio."""
        snapshots = self.snapshots.get(portfolio_id, [])
        return snapshots[-1] if snapshots else None

    def delete_snapshots(self, portfolio_id: UUID) -> bool:
        """Delete all snapshots for a portfolio."""
        if portfolio_id in self.snapshots:
            del self.snapshots[portfolio_id]
            return True
        return False
