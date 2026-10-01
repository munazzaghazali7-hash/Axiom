from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://dataintel:dataintel@localhost:5432/dataintel"

    @field_validator("database_url", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    @field_validator("celery_broker_url", mode="after")
    @classmethod
    def assemble_broker_url(cls, v: str, info: Any) -> str:
        if v:
            return v
        return info.data.get("redis_url", "redis://localhost:6379/0")

    @field_validator("celery_result_backend", mode="after")
    @classmethod
    def assemble_result_backend(cls, v: str, info: Any) -> str:
        if v:
            return v
        return info.data.get("redis_url", "redis://localhost:6379/0")


    # AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    # Search
    tavily_api_key: str = ""
    serper_api_key: str = ""

    # Storage
    storage_backend: str = "local"
    storage_local_path: str = "./data/snapshots"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "change-me-in-production"


settings = Settings()
