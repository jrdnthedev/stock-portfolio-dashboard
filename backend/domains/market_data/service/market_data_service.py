import threading
import time

from ..models.models import Fundamental
from .fundamentals_adapter import FundamentalsAdapter
from .pricing_adapter import PricingAdapter


class MarketDataService:
    def __init__(self, kafka_bootstrap_servers: list[str], price_topic: str) -> None:
        self.pricing_adapter = PricingAdapter(kafka_bootstrap_servers, price_topic)
        self.fundamentals_adapter = FundamentalsAdapter()
        self._simulation_thread: threading.Thread | None = None
        self._stop_simulation = threading.Event()

    def get_fundamental_snapshot(self, ticker_id: int, period: str) -> Fundamental:
        return self.fundamentals_adapter.get_fundamental_snapshot(ticker_id, period)

    def start_price_simulation(
        self, ticker_id: int, start_date: str, days: int = 1, interval_sec: float = 1.0
    ) -> None:
        """
        Starts a background thread that simulates price ticks and feeds Kafka.
        """

        def simulation_loop() -> None:
            for _ in range(days):
                if self._stop_simulation.is_set():
                    break
                self.pricing_adapter.generate_mock_ohlcv(ticker_id, start_date, days=1)
                time.sleep(interval_sec)

        self._stop_simulation.clear()
        self._simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        self._simulation_thread.start()

    def stop_price_simulation(self) -> None:
        """
        Stops the price simulation loop.
        """
        self._stop_simulation.set()
        if self._simulation_thread:
            self._simulation_thread.join()
            self._simulation_thread = None
