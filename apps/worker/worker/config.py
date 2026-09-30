from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://dataintel:dataintel@localhost:5432/dataintel"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    tavily_api_key: str = ""
    serper_api_key: str = ""

    storage_backend: str = "local"
    storage_local_path: str = "./data/snapshots"


settings = Settings()
