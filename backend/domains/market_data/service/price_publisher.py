import threading
import time
from collections.abc import Sequence
from uuid import UUID

from .pricing_adapter import PricingAdapter


class PricePublisher:
    def __init__(
        self,
        kafka_bootstrap_servers: list[str],
        topic: str = "market.prices.live",
        interval_sec: float = 5.0,
    ):
        self.pricing_adapter = PricingAdapter(kafka_bootstrap_servers, topic)
        self.interval_sec = interval_sec
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self, ticker_ids: Sequence[UUID], start_date: str) -> None:
        """
        Start publishing PriceUpdated events for each ticker at a fixed interval.
        """

        def run() -> None:
            while not self._stop_event.is_set():
                for ticker_id in ticker_ids:
                    if self._stop_event.is_set():
                        break
                    self.pricing_adapter.generate_mock_ohlcv(ticker_id, start_date, days=1)
                time.sleep(self.interval_sec)

        self._stop_event.clear()
        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """
        Stop publishing events and cleanup resources.
        """
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        # Close the pricing adapter and Kafka producer
        self.pricing_adapter.close()
