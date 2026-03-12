from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Schedule system"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/schedule_system"


settings = Settings()
