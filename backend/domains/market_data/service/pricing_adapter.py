import json
import random
from datetime import datetime, timedelta

from kafka import KafkaProducer

from ..models.models import PricePoint


class PricingAdapter:
    def __init__(self, kafka_bootstrap_servers: list[str], topic: str):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self.topic = topic

    def generate_mock_ohlcv(self, ticker_id: int, start_date: str, days: int = 1) -> None:
        """
        Generate mock OHLCV data for a given ticker and date range.
        """
        date = datetime.strptime(start_date, "%Y-%m-%d")
        price = random.uniform(100, 500)
        for _ in range(days):
            open_ = price
            high = open_ + random.uniform(0, 10)
            low = open_ - random.uniform(0, 10)
            close = random.uniform(low, high)
            volume = random.randint(1000, 10000)
            price_point = PricePoint(
                id=random.randint(1, 1_000_000),
                ticker_id=ticker_id,
                date=date.strftime("%Y-%m-%d"),
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
            self.publish_price_updated(price_point)
            date += timedelta(days=1)
            price = close

    def publish_price_updated(self, price_point: PricePoint) -> None:
        event = {"event": "PriceUpdated", "data": price_point.model_dump()}
        self.producer.send(self.topic, event)
        self.producer.flush()
