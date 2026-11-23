import sys

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "settings"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "BiletFlow"
    IS_DEV_ENV: bool = True

    # DB — required when IS_DEV_ENV is False
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SERVER: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_PORT: int = 5432
    SQLITE_FILE_NAME: str = "database.sqlite"
    DB_ECHO: bool = False

    # Auth
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    FRONTEND_URL: str = "http://localhost:5173"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 1025
    # Empty for Mailpit. Real providers (port 587) need STARTTLS and a login.
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    MAIL_FROM: str = "no-reply@biletflow.dev"

    # Unpaid checkouts hold inventory this long before the reservation is released (SRS 4.6).
    ORDER_HOLD_MINUTES: int = 15
    # How often the background sweeper looks for expired holds; 0 disables it.
    ORDER_SWEEP_INTERVAL_SECONDS: int = 60

    DEFAULT_CURRENCY: str = "KZT"
    DEFAULT_TIMEZONE: str = "Asia/Almaty"

    @property
    def database_url(self) -> str:
        if self.IS_DEV_ENV and not self.POSTGRES_SERVER:
            return f"sqlite:///{self.SQLITE_FILE_NAME}"

        return (
            "postgresql+psycopg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    @model_validator(mode="after")
    def _validate_required_keys(self) -> "Settings":
        """Crash early with a clear message if required env vars are missing."""
        missing: list[str] = []

        if not self.IS_DEV_ENV:
            for key in (
                "POSTGRES_USER",
                "POSTGRES_PASSWORD",
                "POSTGRES_SERVER",
                "POSTGRES_DB",
                "JWT_SECRET",
            ):
                if not getattr(self, key):
                    missing.append(key)

        if missing:
            print(
                f"\n Missing required environment variables: {', '.join(missing)}\n"
                "   Set them in your .env file or pass via environment.\n",
                file=sys.stderr,
            )
            raise SystemExit(1)

        return self


settings = Settings()
