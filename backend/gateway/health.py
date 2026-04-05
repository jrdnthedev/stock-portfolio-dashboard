"""Health check endpoint for monitoring service dependencies."""

import logging
from datetime import UTC, datetime
from typing import Any

from kafka import KafkaAdminClient
from kafka.errors import KafkaError
from sqlalchemy import text

try:
    from backend.config import get_settings
    from backend.database.database import engine
    from backend.gateway.cache import get_cache_service
except ImportError:
    from config import get_settings
    from database.database import engine
    from gateway.cache import get_cache_service

logger = logging.getLogger(__name__)


def check_postgres() -> dict[str, Any]:
    """Check PostgreSQL database connectivity and responsiveness."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            _ = result.fetchone()
            return {
                "status": "healthy",
                "message": "PostgreSQL connection successful",
                "response_time_ms": 0,
            }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"PostgreSQL connection failed: {str(e)}",
            "response_time_ms": 0,
        }


def check_redis() -> dict[str, Any]:
    """Check Redis connectivity and responsiveness."""
    try:
        cache = get_cache_service()
        if cache.ping():
            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "response_time_ms": 0,
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Redis ping failed",
                "response_time_ms": 0,
            }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
            "response_time_ms": 0,
        }


def check_kafka() -> dict[str, Any]:
    """Check Kafka broker connectivity."""
    try:
        settings = get_settings()
        admin_client = KafkaAdminClient(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            request_timeout_ms=5000,
        )

        # List topics to verify connection
        topics = admin_client.list_topics()
        admin_client.close()

        return {
            "status": "healthy",
            "message": f"Kafka broker connected ({len(topics)} topics)",
            "response_time_ms": 0,
        }
    except KafkaError as e:
        logger.error(f"Kafka health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Kafka connection failed: {str(e)}",
            "response_time_ms": 0,
        }
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Kafka connection failed: {str(e)}",
            "response_time_ms": 0,
        }


def get_health_status() -> dict[str, Any]:
    """
    Aggregate health check for all services.

    Returns a comprehensive health status including:
    - Overall system health
    - Individual service statuses
    - Timestamp of the check
    """
    postgres_health = check_postgres()
    redis_health = check_redis()
    kafka_health = check_kafka()

    # Determine overall status
    all_healthy = all(
        check["status"] == "healthy" for check in [postgres_health, redis_health, kafka_health]
    )

    overall_status = "healthy" if all_healthy else "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime.now(UTC).isoformat(),
        "services": {
            "postgres": postgres_health,
            "redis": redis_health,
            "kafka": kafka_health,
        },
    }
