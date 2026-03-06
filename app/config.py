"""
app/config.py — Application settings (Member 1 Infrastructure)
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Courier Core — Smart Assignment Engine"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False

    # Database (Member 1 Tool: PostgreSQL)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/courier_core"

    # OSRM (Member 1 Tool: Road Distances)
    OSRM_BASE_URL: str = "http://router.project-osrm.org"

    # Security (Architect's Shield)
    API_KEY: str = "JANA_COURIER_2026"


@lru_cache
def get_settings() -> Settings:
    return Settings()
