from functools import lru_cache
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _validate_database_url(url: str) -> str:
    if url.startswith("sqlite"):
        return url
    parsed = urlparse(url)
    if not parsed.hostname or "@" in (parsed.hostname or ""):
        raise ValueError(
            "DATABASE_URL looks malformed. Use the Supabase connection URI exactly as copied "
            "(postgresql://postgres.[ref]:[password]@....pooler.supabase.com:6543/postgres). "
            "Do not include your email in the URL. URL-encode special characters in the password."
        )
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Smart Plant Doctor API"
    api_v1_prefix: str = "/api/v1"

    # Supabase — set DATABASE_URL to your Supabase Postgres connection string (Session pooler)
    supabase_url: str = ""
    supabase_jwt_secret: str = ""

    database_url: str = "sqlite:///./data/app.db"

    cors_origins: str = "http://localhost:5173,http://localhost:3000,https://smart-plant-dr.vercel.app"

    uploads_dir: str = "uploads"
    model_path: str = "../ai/exports/smart_plant_doctor_model.pth"
    confidence_threshold: float = 0.70
    model_temperature: float = 1.0

    gemini_api_key: str = ""
    gemini_chat_models: str = "gemma-4-31b-it,gemma-4-4b-it,gemma-4-26b-a4b-it"

    blynk_auth_token: str = ""
    blynk_server: str = "https://blynk.cloud"

    public_api_url: str = "http://localhost:8000"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        return _validate_database_url(value)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_supabase_auth(self) -> bool:
        return bool(self.supabase_jwt_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
