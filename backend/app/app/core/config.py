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

    PROJECT_NAME: str = "BeMore"
    API_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    host: str = "0.0.0.0"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = True

    # Current environment
    environment: str = "dev"

    USERS_OPEN_REGISTRATION: bool = False

    log_level: LogLevel = LogLevel.INFO

    # Database settings
    POSTGRES_USER: str = "bemore"
    POSTGRES_PASSWORD: str = "changethis"
    POSTGRES_DB: str = "app"

    FIRST_SUPERUSER: str = "admin@localhost.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin"
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    EMAILS_ENABLED: bool = False
    EMAILS_FROM_NAME: str = "BeMore"
    EMAILS_FROM_EMAIL: str = ""
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    SMTP_HOST: str = ""
    SMTP_PORT: int = 0
    SMTP_TLS: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    EMAIL_TEMPLATES_DIR: str = "bemore/email-templates/build"

    # requests settings
    REQUESTS_BATCH_SIZE: int = 2
    CRAWL_INTERVAL: int = 60 * 60 * 24 * 7  # 1 week

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
