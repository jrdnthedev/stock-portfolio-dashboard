import json
import logging
import random
import time
from datetime import datetime, timedelta
from uuid import UUID

from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

from ..models.models import PricePoint

logger = logging.getLogger(__name__)


class PricingAdapter:
    def __init__(self, kafka_bootstrap_servers: list[str], topic: str, max_retries: int = 5):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic = topic
        self.max_retries = max_retries
        self.producer = self._create_producer_with_retry()

    def _create_producer_with_retry(self) -> KafkaProducer:
        """Create Kafka producer with exponential backoff retry logic."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Attempting to connect to Kafka (attempt {attempt}/{self.max_retries})..."
                )
                producer = KafkaProducer(
                    bootstrap_servers=self.kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    request_timeout_ms=10000,
                    max_block_ms=10000,
                )
                logger.info("Successfully connected to Kafka")
                return producer
            except (NoBrokersAvailable, KafkaError) as e:
                if attempt == self.max_retries:
                    logger.error(
                        f"Failed to connect to Kafka after {self.max_retries} attempts: {e}"
                    )
                    raise
                wait_time = 2**attempt  # Exponential backoff: 2, 4, 8, 16, 32 seconds
                logger.warning(
                    f"Kafka connection failed (attempt {attempt}/{self.max_retries}): {e}"
                )
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        raise RuntimeError("Failed to create Kafka producer")

    def generate_mock_ohlcv(self, ticker_id: UUID, start_date: str, days: int = 1) -> None:
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
        """Publish price update event to Kafka with error handling."""
        try:
            # Use model_dump_json() and parse back to dict to ensure proper JSON serialization of UUIDs
            price_data = json.loads(price_point.model_dump_json())
            event = {"event": "PriceUpdated", "data": price_data}
            future = self.producer.send(self.topic, event)
            # Wait for send to complete with timeout
            future.get(timeout=10)
        except Exception as e:
            logger.error(f"Failed to publish price update for ticker {price_point.ticker_id}: {e}")

    def close(self) -> None:
        """Close the Kafka producer and cleanup resources."""
        if self.producer:
            logger.info("Closing Kafka producer...")
            self.producer.flush(timeout=5)
            self.producer.close(timeout=5)
            logger.info("Kafka producer closed")
