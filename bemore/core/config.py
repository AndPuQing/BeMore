import enum
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, enum.Enum):  # noqa: WPS600
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    API_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BEMORE_",
        env_file_encoding="utf-8",
    )

    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./bemore.db"
    FIRST_SUPERUSER: str = "admin@localhost"
    FIRST_SUPERUSER_PASSWORD: str = "admin"


settings = Settings()
