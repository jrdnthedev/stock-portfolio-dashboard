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
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_prefix: str = "stock-portfolio"

    class ConfigDict:
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Create a settings instance for easy access
settings = get_settings()
