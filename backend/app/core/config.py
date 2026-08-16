from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Personal Asset Portfolio API"
    environment: str = "development"
    log_level: str = "INFO"
    demo_mode: bool = True
    database_url: str = "postgresql+asyncpg://portfolio:portfolio@localhost:5433/portfolio"
    frontend_url: str = "http://localhost:3001"

    notion_api_key: str | None = None
    notion_api_version: str = "2026-03-11"
    notion_accounts_data_source_id: str | None = None
    notion_assets_data_source_id: str | None = None
    notion_savings_data_source_id: str | None = None
    notion_debts_data_source_id: str | None = None
    notion_goals_data_source_id: str | None = None
    notion_allocation_targets_data_source_id: str | None = None
    notion_webhook_verification_token: str | None = None

    toss_client_id: str | None = None
    toss_client_secret: str | None = None
    toss_base_url: str = "https://openapi.tossinvest.com"

    external_api_timeout_seconds: float = Field(default=12.0, ge=1, le=60)
    external_api_max_retries: int = Field(default=3, ge=0, le=5)

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def notion_data_sources(self) -> dict[str, str | None]:
        return {
            "accounts": self.notion_accounts_data_source_id,
            "assets": self.notion_assets_data_source_id,
            "savings": self.notion_savings_data_source_id,
            "debts": self.notion_debts_data_source_id,
            "goals": self.notion_goals_data_source_id,
            "allocation_targets": self.notion_allocation_targets_data_source_id,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
