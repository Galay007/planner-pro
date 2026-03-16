from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from cryptography.fernet import Fernet


def get_env_filename():
    runtime_env = os.getenv("ENV")
    return f".env.{runtime_env}" if runtime_env else ".env"

class Settings(BaseSettings):    
    model_config = SettingsConfigDict(
        env_file=get_env_filename(),
        env_file_encoding="utf-8"
    )
    app_name: str
    database_url: str
    fernet_key: str

settings = Settings()

if not settings.fernet_key:
    raise RuntimeError("FERNET_KEY not set")

fernet = Fernet(settings.fernet_key.encode())