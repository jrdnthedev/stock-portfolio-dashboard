import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file from the backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # Stock API settings
    stock_api_key: str = ""
    stock_api_url: str = ""

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DEBUG: bool = True

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_default_ttl: int = 1800  # 30 minutes

    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9093"
    kafka_topic_prefix: str = "stock-portfolio"

    # JWT Authentication settings
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "your-secret-key-CHANGE-THIS-IN-PRODUCTION-min-32-characters-long",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30  # 30 minutes
    jwt_refresh_token_expire_days: int = 7  # 7 days

    class ConfigDict:
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Create a settings instance for easy access
settings = get_settings()
