from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./career_platform.db"
    snapshot_dir: Path = Path("./snapshots")
    resend_api_key: str = ""
    contact_from: str = "website@example.com"
    contact_to: str = ""
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
