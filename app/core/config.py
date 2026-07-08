from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env file.

    pydantic-settings validates types at startup: if a required variable is
    missing or malformed, the app fails fast with a clear error instead of
    crashing later at first use.
    """

    # Anchored to the project root so the app finds .env from any cwd.
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    # Cloud platforms (Render, Railway...) provide one ready-made connection
    # URL instead of separate credentials. When set, it wins over POSTGRES_*.
    database_url_env: str = Field("", alias="DATABASE_URL")

    postgres_user: str = ""
    postgres_password: str = ""
    postgres_db: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Email notifications via SMTP (e.g. Gmail: smtp.gmail.com + app password)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notify_email_to: str = ""

    # Comma-separated keywords; a new job is notified if its title or tags
    # contain at least one of them. Empty = notify nothing.
    match_keywords: str = ""
    scrape_interval_hours: int = 6

    @property
    def keywords_list(self) -> list[str]:
        return [k.strip().lower() for k in self.match_keywords.split(",") if k.strip()]

    @property
    def database_url(self) -> str:
        if self.database_url_env:
            # Normalize the scheme so SQLAlchemy picks the psycopg driver
            # (cloud platforms hand out postgres:// or postgresql:// URLs).
            url = self.database_url_env
            for prefix in ("postgres://", "postgresql://"):
                if url.startswith(prefix):
                    return url.replace(prefix, "postgresql+psycopg://", 1)
            return url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
