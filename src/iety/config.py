"""Pydantic settings configuration for IETY."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    user: str = Field(default="iety", description="PostgreSQL user")
    password: SecretStr = Field(default=SecretStr("iety_dev_password"))
    db: str = Field(default="iety", alias="database", description="PostgreSQL database name")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max pool overflow")

    @property
    def async_url(self) -> str:
        """Async SQLAlchemy connection URL."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def sync_url(self) -> str:
        """Sync SQLAlchemy connection URL (for Alembic)."""
        return (
            f"postgresql://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class VoyageSettings(BaseSettings):
    """Voyage AI embedding settings."""

    model_config = SettingsConfigDict(env_prefix="VOYAGE_")

    api_key: Optional[SecretStr] = Field(default=None, description="Voyage AI API key")
    model: str = Field(default="voyage-3.5-lite", description="Embedding model")
    batch_size: int = Field(default=128, description="Texts per embedding batch")
    rate_limit: int = Field(default=100, description="Requests per second")
    cost_per_million_tokens: float = Field(default=0.02, description="Cost per 1M tokens")


class SECSettings(BaseSettings):
    """SEC EDGAR API settings."""

    model_config = SettingsConfigDict(env_prefix="SEC_")

    user_agent: str = Field(
        default="IETY Research Bot (contact@example.com)",
        description="Required User-Agent header for SEC EDGAR",
    )
    rate_limit: int = Field(default=10, description="Requests per second")
    base_url: str = Field(
        default="https://data.sec.gov", description="SEC EDGAR data URL"
    )


class CourtListenerSettings(BaseSettings):
    """CourtListener API settings."""

    model_config = SettingsConfigDict(env_prefix="COURTLISTENER_")

    api_key: Optional[SecretStr] = Field(default=None, description="CourtListener API key")
    rate_limit: int = Field(default=5000, description="Requests per hour")
    base_url: str = Field(
        default="https://www.courtlistener.com/api/rest/v3",
        description="CourtListener API base URL",
    )


class USASpendingSettings(BaseSettings):
    """USASpending API settings."""

    model_config = SettingsConfigDict(env_prefix="USASPENDING_")

    base_url: str = Field(
        default="https://api.usaspending.gov/api/v2",
        description="USASpending API base URL",
    )
    bulk_download_url: str = Field(
        default="https://files.usaspending.gov",
        description="USASpending bulk download URL",
    )
    # ICE/CBP Treasury Account Symbols
    target_account_codes: list[str] = Field(
        default=["070-0540", "070-0543", "070-0532"],
        description="Treasury account codes for ICE/CBP",
    )


class GDELTSettings(BaseSettings):
    """GDELT data settings."""

    model_config = SettingsConfigDict(env_prefix="GDELT_")

    csv_url: str = Field(
        default="http://data.gdeltproject.org/gdeltv2/lastupdate.txt",
        description="GDELT last update URL",
    )
    poll_interval_seconds: int = Field(
        default=900, description="Polling interval (15 minutes)"
    )
    use_bigquery: bool = Field(default=False, description="Use BigQuery instead of CSV")
    bigquery_project: Optional[str] = Field(default=None, description="GCP project for BigQuery")


class BudgetSettings(BaseSettings):
    """Budget and cost control settings."""

    model_config = SettingsConfigDict(env_prefix="BUDGET_")

    monthly_limit: float = Field(default=50.0, description="Monthly budget limit in USD")
    warning_threshold: float = Field(default=0.90, description="Warning at 90% of budget")
    halt_threshold: float = Field(default=0.95, description="Halt at 95% of budget")

    @field_validator("warning_threshold", "halt_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if not 0 < v <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return v


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Environment
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    voyage: VoyageSettings = Field(default_factory=VoyageSettings)
    sec: SECSettings = Field(default_factory=SECSettings)
    courtlistener: CourtListenerSettings = Field(default_factory=CourtListenerSettings)
    usaspending: USASpendingSettings = Field(default_factory=USASpendingSettings)
    gdelt: GDELTSettings = Field(default_factory=GDELTSettings)
    budget: BudgetSettings = Field(default_factory=BudgetSettings)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
